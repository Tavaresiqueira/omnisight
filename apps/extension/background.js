chrome.action.onClicked.addListener((tab) => {
  if (Number.isInteger(tab.id)) {
    chrome.tabs.create({ url: `${chrome.runtime.getURL('scan.html')}?tab=${tab.id}` });
  }
});
