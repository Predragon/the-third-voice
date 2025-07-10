export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Only POST method is allowed" });
  }

  const userInput = req.body?.message;
  const tone = req.body?.tone || "Kind";

  if (!userInput) {
    return res.status(400).json({ error: "Message content is required." });
  }

  const prompt = `Rewrite the following message in a ${tone.toLowerCase()} tone:\n\n${userInput}`;

  try {
    const hfResponse = await fetch("https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-common_gen", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.HF_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: prompt }),
    });

    const result = await hfResponse.json();

    // Check if result contains error from Hugging Face
    if (result.error) {
      console.error("Hugging Face API returned error:", result.error);
      // Send the specific Hugging Face error to the frontend
      return res.status(500).json({ error: `Hugging Face API Error: ${result.error.toString()}` });
    }

    const output = result?.[0]?.generated_text || "No result from model";
    res.status(200).json({ result: output }); // Your frontend expects 'result'

  } catch (err) {
    console.error("API call failed:", err);
    // **CRITICAL TEMPORARY DEBUGGING LINE:** Send the detailed error message from 'err'
    return res.status(500).json({ error: `API Call Failed (Backend): ${err.message || 'Unknown error'}` });
  }
}
