export type AccountType = "extension_user" | "platform_developer";

export type AuthResponse = {
  token: string;
  user: {
    id: string;
    email: string;
    display_name: string;
    account_type: AccountType;
    is_demo: boolean;
  };
  organization: {
    id: string;
    name: string;
    slug: string;
    account_type: AccountType;
  } | null;
  role: "owner" | "member" | "viewer" | null;
};

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");

function firstErrorMessage(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map(firstErrorMessage).find(Boolean) ?? null;
  }
  if (value && typeof value === "object") {
    if ('message' in value && typeof value.message === 'string') return value.message;
    return Object.values(value).map(firstErrorMessage).find(Boolean) ?? null;
  }
  return null;
}

export async function postAuth(
  path: "auth/login/" | "auth/register/",
  payload: Record<string, string>,
): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      firstErrorMessage(data) ?? "Não foi possível concluir. Tente novamente.",
    );
  }
  return data as AuthResponse;
}

export async function postDemoLogin(accountType: AccountType): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/demo/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ account_type: accountType }),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(firstErrorMessage(data) ?? "Não foi possível abrir a conta demo.");
  }
  return data as AuthResponse;
}

export async function getCurrentUser(token: string): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/me/`, {
    headers: { Authorization: `Token ${token}` },
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(firstErrorMessage(data) ?? "Sua sessão expirou. Entre novamente.");
  }
  return data as AuthResponse;
}

export type Site = { id: string; displayName: string; normalizedUrl: string; createdAt: string };
export async function getSites(token: string): Promise<Site[]> {
 const response=await fetch(`${API_URL}/sites/`,{headers:{Authorization:`Token ${token}`}});
 const data=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(firstErrorMessage(data)??'Não foi possível carregar os sites.');
 return data.items;
}
export async function createSite(token: string,payload:{displayName:string;url:string}):Promise<Site>{
 const response=await fetch(`${API_URL}/sites/`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Token ${token}`},body:JSON.stringify(payload)});
 const data=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(data?.message??firstErrorMessage(data)??'Não foi possível cadastrar o site.');
 return data;
}

export type Scan = {id:string;siteId:string;status:'queued'|'running'|'completed'|'failed'|'cancelled';attempts:number;errorCode:string;requestedAt:string;startedAt:string|null;completedAt:string|null;correlationId:string};
export type ScanCheck={id:string;title:string;status:'issue'|'review'|'clear'|'na';impact:string;criteria:string[];count:number;help:string;examples:{selector:string;html:string;summary:string}[]};
export type VisualCapture={name:string;accessibilityChecks?:ScanCheck[];viewport:{width:number;height:number};truncated:boolean;checks:{id:string;title:string;criterion:string;status:'review'|'clear';count:number;help:string;examples:{selector:string;rect:{x:number;y:number;width:number;height:number}}[]}[];screenshot:{mime:'image/jpeg';dataBase64:string}|null;screenshotWarning?:string};
export type ScanReport={schemaVersion:number;engine:string;engineVersion:string;mode:string;pages:{url:string;title:string;checks:ScanCheck[];limitations:string[];visual?:VisualCapture[];styleCoverage?:{loaded:number;skipped:number}}[];coverage:{pageLimit:number;externalResources:boolean;pageScripts:boolean;completeWcagAudit:boolean}};
async function scanRequest<T>(path:string,token:string,init:RequestInit={}):Promise<T>{
 const response=await fetch(`${API_URL}/${path}`,{...init,headers:{'Content-Type':'application/json',Authorization:`Token ${token}`,...init.headers}});
 const data=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(firstErrorMessage(data)??'Não foi possível concluir a operação do scan.');
 return data as T;
}
export const getScans=(token:string,siteId:string,signal?:AbortSignal)=>scanRequest<{items:Scan[]}>(`sites/${siteId}/scans/`,token,{signal});
export const requestScan=(token:string,siteId:string,key:string)=>scanRequest<Scan>(`sites/${siteId}/scans/`,token,{method:'POST',headers:{'Idempotency-Key':key},body:JSON.stringify({viewport:'desktop'})});
export const changeScan=(token:string,id:string,action:'cancel'|'retry')=>scanRequest<Scan>(`scans/${id}/actions/`,token,{method:'POST',body:JSON.stringify({action})});
export const getScanReport=(token:string,id:string)=>scanRequest<ScanReport>(`scans/${id}/report/`,token);
export const deleteScan=(token:string,id:string)=>scanRequest<void>(`scans/${id}/`,token,{method:'DELETE'});
export const closeAccount=(token:string,password:string,confirmation:string)=>scanRequest<void>('auth/account/close/',token,{method:'POST',body:JSON.stringify({password,confirmation})});
export const closeOrganization=(token:string,id:string,password:string,confirmation:string)=>scanRequest<void>(`organizations/${id}/`,token,{method:'POST',body:JSON.stringify({password,confirmation})});
export const getAccountExport=(token:string)=>scanRequest<Record<string,unknown>>('auth/account/export/',token);
