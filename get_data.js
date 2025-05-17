const axios = require("axios");
const { KoiiStorageClient } = require("@_koii/storage-task-sdk");
const storageClient = new KoiiStorageClient(undefined, undefined, false);

async function fetchCidFromGetFile(cid, fileName) {
  try {
    const blob = await storageClient.getFile(cid, fileName);
    const text = await blob.text(); // Convert Blob to text
    const data = JSON.parse(text);  // Parse text to JSON
    return data;
  } catch (error) {
    console.log(`SDK fetch failed for CID ${cid}: ${error.message}`);
    return null;
  }
}

async function directFetchCid(cid, fileName) {
  try {
    const url = `https://ipfs-gateway.koii.live/ipfs/${cid}/${fileName}`;
    const response = await axios.get(url, { timeout: 530000 });
    if (response.status === 200 || response.status === 304) {
      return response.data;
    } else {
      console.log(`Received status ${response.status} for URL ${url}`);
    }
  } catch (error) {
    console.log(`Direct fetch failed for CID ${cid}: ${error.message}`);
  }
  return null;
}

async function fetchCIDData(cid, fileName, maxRetries = 2, retryDelay = 3000) {
  const data = await fetchCidFromGetFile(cid, fileName);
  if (data) {
    return data;
  }

  // Fallback to direct fetch
  const dataDirect = await directFetchCid(cid, fileName);
  if (dataDirect) {
    return dataDirect;
  }

  return null;
}

// 🔽 Replace with your CID and filename
const cid = "bafybeieywupm42iyswchlz3aohw5jyhvyw5ujdu6u4udnoyxbm7q7x5wwa";
const fileName = "submission.json";

(async () => {
  const data = await fetchCIDData(cid, fileName);
  if (data) {
    console.log("✅ Data retrieved:\n", data);
  } else {
    console.log("❌ Failed to retrieve data from all sources.");
  }
})();
