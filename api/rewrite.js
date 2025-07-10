// pages/api/rewrite.js

export default async function handler(req, res) {
  // 1. Input Validation
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Only POST method is allowed." });
  }

  const userInput = req.body?.message;
  const tone = req.body?.tone || "Kind";

  if (!userInput) {
    return res.status(400).json({ error: "Message content is required." });
  }

  // 2. Define Prompt
  const prompt = `Rewrite the following message in a ${tone}, emotionally intelligent tone:\n\n${userInput}`;

  // 3. Temporary Debugging for API Key (Keep this for now!)
  console.log("Attempting API call to Hugging Face.");
  const apiKey = process.env.HF_API_KEY;
  if (!apiKey) {
    console.error("HF_API_KEY is UNDEFINED in environment!");
    return res.status(500).json({ error: "Server error: API Key not configured." });
  } else {
    console.log(`HF_API_KEY length: ${apiKey.length}`);
    console.log(`HF_API_KEY starts with: ${apiKey.substring(0, 5)}...`); // Log first 5 chars
  }

  // 4. API Call with Try-Catch for Error Handling
  try {
    const hfResponse = await fetch("https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-common_gen", { // <-- CORRECT MODEL HERE
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`, // Use the local apiKey variable
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: prompt }),
    });

    const result = await hfResponse.json();

    // Check if Hugging Face API returned its own error (e.g., rate limit, invalid input)
    if (result.error) {
      console.error("Hugging Face API returned error:", result.error);
      return res.status(500).json({ error: `Hugging Face API Error: ${result.error.toString()}` });
    }

    const output = result?.[0]?.generated_text || "No result from model";

    // 5. Send Response - Match Frontend Expectation (data.result)
    res.status(200).json({ result: output }); // <-- Ensure this is 'result' for your frontend

  } catch (err) {
    // 6. Catch any network or other unexpected errors from fetch
    console.error("API Call Failed (Backend unexpected error):", err);
    return res.status(500).json({ error: `API Call Failed (Backend): ${err.message || 'Unknown error'}` });
  }
}
