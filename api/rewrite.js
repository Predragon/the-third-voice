// /api/rewrite.js

export default async function handler(req, res) {
  // 1. Only allow POST requests
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Only POST method is allowed." });
  }

  // 2. Extract inputs
  const userInput = req.body?.message;
  const tone = req.body?.tone || "Kind";

  if (!userInput) {
    return res.status(400).json({ error: "Message content is required." });
  }

  // 3. Prepare the prompt
  const prompt = `Rewrite the following message in a ${tone}, emotionally intelligent tone:\n\n${userInput}`;

  // 4. API key check
  const apiKey = process.env.HF_API_KEY;
  if (!apiKey) {
    console.error("HF_API_KEY is undefined in environment variables.");
    return res.status(500).json({ error: "Server error: API Key not configured." });
  }

  // 5. Make request to Hugging Face
  try {
    const hfResponse = await fetch("https://api-inference.huggingface.co/models/google/flan-t5-small", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: prompt }),
    });

    // Optional debug logging
    const raw = await hfResponse.text();
    console.log("Raw HF response:", raw);

    // Parse JSON manually
    let result;
    try {
      result = JSON.parse(raw);
    } catch (jsonErr) {
      console.error("JSON parse error:", jsonErr);
      return res.status(500).json({ error: "Hugging Face returned invalid JSON." });
    }

    // Check for Hugging Face error in response
    if (result.error) {
      console.error("Hugging Face API returned error:", result.error);
      return res.status(500).json({ error: `Hugging Face API Error: ${result.error.toString()}` });
    }

    // Get model output
    const output = result?.[0]?.generated_text || "No result from model";

    // 6. Return final result to frontend
    return res.status(200).json({ result: output });

  } catch (err) {
    console.error("API Call Failed:", err);
    return res.status(500).json({ error: `API Call Failed (Backend): ${err.message || "Unknown error"}` });
  }
}
