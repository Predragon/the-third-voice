export default async function handler(req, res) {
  // ... (existing code: method check, input validation, prompt creation)

  // --- START TEMPORARY DEBUGGING CODE ---
  console.log("Attempting API call to Hugging Face.");
  const apiKey = process.env.HF_API_KEY;
  if (!apiKey) {
    console.error("HF_API_KEY is UNDEFINED in environment!");
  } else {
    console.log(`HF_API_KEY length: ${apiKey.length}`);
    console.log(`HF_API_KEY starts with: ${apiKey.substring(0, 5)}...`); // Log first 5 chars
  }
  // --- END TEMPORARY DEBUGGING CODE ---

  try {
    const hfResponse = await fetch("https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-common_gen", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`, // Use the local apiKey variable
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: prompt }),
    });

    // ... (rest of your existing code for handling hfResponse and catch block)
  } catch (err) {
    console.error("API Call Failed (Backend):", err);
    return res.status(500).json({ error: `API Call Failed (Backend): ${err.message || 'Unknown error'}` });
  }
}
