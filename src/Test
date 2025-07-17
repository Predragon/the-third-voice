document.getElementById("message-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const input = document.getElementById("user-input").value;
  const output = document.getElementById("output");
  output.innerText = "Rewriting...";

  const response = await fetch("/api/rewrite", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text: input })
  });

  const data = await response.json();
  output.innerText = data.result || "Something went wrong.";
});
