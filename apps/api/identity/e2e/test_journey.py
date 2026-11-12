"""Real UI, HTTP API, DB, queue, browser service and axe; fixture replaces target network only."""
import os
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

from django.test import LiveServerTestCase, override_settings
from identity.models import Scan, ScanReport
from identity.pipeline import collect_and_analyze
from identity.ssrf import SafeFetchResponse
from identity.worker import process_next


@skipUnless(os.environ.get('RUN_E2E_TESTS') == '1', 'E2E exige build web, PostgreSQL e serviço browser; job e2e do CI.')
@override_settings(ROOT_URLCONF='identity.e2e.urls', ALLOWED_HOSTS=['localhost', 'testserver'])
class CriticalJourneyTests(LiveServerTestCase):
    def test_registration_login_scan_report_and_tenant_isolation(self):
        from playwright.sync_api import sync_playwright, expect

        artifacts = Path(os.environ.get('E2E_ARTIFACTS', 'artifacts/e2e'))
        artifacts.mkdir(parents=True, exist_ok=True)
        html = Path(__file__).with_name('fixtures').joinpath('barriers.html').read_bytes()
        fixture = SafeFetchResponse('https://example.com/', 200, {'content-type': 'text/html'}, html, 0)
        with sync_playwright() as playwright:
            executable = os.environ.get('CHROMIUM_EXECUTABLE')
            browser = playwright.chromium.launch(headless=True, chromium_sandbox=True, **({'executable_path': executable} if executable else {}))
            context = browser.new_context(viewport={'width': 1280, 'height': 900})
            context.tracing.start(screenshots=True, snapshots=True)
            page = context.new_page()
            page.set_default_timeout(15000)
            try:
                page.goto(self.live_server_url)
                page.get_by_role('tab', name='Criar conta').click()
                page.get_by_role('radio', name='Analisar uma plataforma').check()
                page.get_by_label('Como podemos chamar você?').fill('Teste E2E')
                page.get_by_label('E-mail', exact=True).fill('journey@example.com')
                page.get_by_label('Senha', exact=True).fill('E2E-only-strong-pass-2026!')
                page.get_by_role('button', name='Criar meu espaço').click()
                expect(page.get_by_role('heading', name='Visão da plataforma')).to_be_visible()
                page.get_by_role('button', name='Sair', exact=True).click()
                page.get_by_label('E-mail', exact=True).fill('journey@example.com')
                page.get_by_label('Senha', exact=True).fill('E2E-only-strong-pass-2026!')
                page.get_by_role('button', name='Entrar na plataforma').click()
                expect(page.get_by_role('heading', name='Seus sites')).to_be_visible()
                page.get_by_label('Nome do site', exact=True).fill('Loja E2E')
                page.get_by_label('URL HTTPS', exact=True).fill('https://example.com/')
                # Only external DNS/HTTP collection is deterministic. No API/report mocks.
                with patch('identity.views.resolve_public_destination'):
                    page.get_by_role('button', name='Cadastrar site', exact=True).click()
                    expect(page.get_by_role('link', name='Loja E2E', exact=True)).to_be_visible()
                run = page.get_by_role('button', name='Executar scan', exact=True)
                expect(run).to_be_enabled()
                page.screenshot(path=str(artifacts / '01-workspace.png'), full_page=True)
                run.click()
                expect(page.get_by_text('Último scan: Na fila.', exact=True)).to_be_visible()
                with patch('identity.crawler.fetch_public_url', return_value=fixture), patch('identity.worker.collect_and_analyze', side_effect=collect_and_analyze):
                    self.assertTrue(process_next())
                scan = Scan.objects.get()
                self.assertEqual(scan.status, 'completed', scan.error_code)
                report = ScanReport.objects.get(scan=scan)
                self.assertTrue(any(c['id'] == 'image-alt' and c['status'] == 'issue' for c in report.payload['pages'][0]['checks']))
                expect(page.get_by_role('button', name='Ver relatório')).to_be_visible(timeout=15000)
                page.get_by_role('button', name='Ver relatório').click()
                expect(page.get_by_role('heading', name='Diagnóstico salvo')).to_be_visible()
                expect(page.get_by_role('heading', name='Loja de teste OmniSight')).to_be_visible()
                page.screenshot(path=str(artifacts / '02-report.png'), full_page=True)
                page.reload()
                page.get_by_role('button', name='Ver relatório').click()
                expect(page.get_by_role('heading', name='Diagnóstico salvo')).to_be_visible()
                # Separate authenticated tenant cannot read the persisted snapshot.
                response = context.request.post(self.live_server_url + '/api/auth/register/', data={
                    'email': 'foreign-journey@example.com', 'password': 'Foreign-only-pass-2026!',
                    'display_name': 'Outro espaço', 'account_type': 'platform_developer',
                })
                self.assertEqual(response.status, 201)
                denied = context.request.get(self.live_server_url + f'/api/scans/{scan.id}/report/', headers={'Authorization': 'Token ' + response.json()['token']})
                self.assertEqual(denied.status, 404)
                page.get_by_role('button', name='Excluir scan', exact=True).click()
                page.get_by_role('button', name='Confirmar exclusão', exact=True).click()
                expect(page.get_by_text('Scan e relatório excluídos.', exact=True)).to_be_visible()
                self.assertFalse(ScanReport.objects.exists())
                self.assertFalse(Scan.objects.exists())
            finally:
                page.screenshot(path=str(artifacts / 'last-page.png'), full_page=True)
                context.tracing.stop(path=str(artifacts / 'trace.zip'))
                browser.close()
