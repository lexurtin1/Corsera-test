document.addEventListener("DOMContentLoaded", () => {
  const card = document.getElementById("progress-card");
  if (!card) return;

  const finalizeUrl = card.dataset.finalizeUrl;
  const headline = document.getElementById("progress-headline");
  const resultPanel = document.getElementById("result-panel");
  const downloadJson = document.getElementById("download-json");
  const downloadCsv = document.getElementById("download-csv");

  const segmentMap = {
    kyc: document.querySelector(".segment-kyc"),
    aml: document.querySelector(".segment-aml"),
    ownership: document.querySelector(".segment-ownership"),
    governance: document.querySelector(".segment-governance"),
  };

  const iconMap = {
    kyc: document.querySelector(".icon-kyc"),
    aml: document.querySelector(".icon-aml"),
    ownership: document.querySelector(".icon-ownership"),
    governance: document.querySelector(".icon-governance"),
  };

  const badges = {
    kyc: document.querySelector("[data-segment='kyc'] .badge"),
    aml: document.querySelector("[data-segment='aml'] .badge"),
    ownership: document.querySelector("[data-segment='ownership'] .badge"),
    governance: document.querySelector("[data-segment='governance'] .badge"),
  };

  const timeline = [
    { delay: 1500, key: "kyc" },
    { delay: 3000, key: "aml" },
    { delay: 4500, key: "ownership" },
    { delay: 6000, key: "governance" },
  ];

  let finalized = false;

  function markComplete(key) {
    const segment = segmentMap[key];
    const badge = badges[key];
    const icon = iconMap[key];

    if (segment) {
      segment.classList.add("complete");
    }

    if (badge) {
      badge.classList.remove("pending");
      badge.classList.add("pass");
      badge.textContent = "Pass";
    }

    if (icon) {
      icon.textContent = "✔";
      icon.classList.add("complete");
    }

    if (key === "governance" && !finalized) {
      finalized = true;
      finalizePacket();
    }
  }

  async function finalizePacket() {
    try {
      const response = await fetch(finalizeUrl, {
        method: "POST",
        headers: { "X-Requested-With": "fetch" },
      });
      if (!response.ok) {
        throw new Error("Finalize failed");
      }
      const data = await response.json();
      if (data && data.ok) {
        headline.textContent = "Compliance Packet Ready ✅";
        downloadJson.href = data.json_url;
        downloadCsv.href = data.csv_url;
        resultPanel.classList.remove("hidden");
      }
    } catch (err) {
      console.error(err);
    }
  }

  timeline.forEach((step) => {
    setTimeout(() => markComplete(step.key), step.delay);
  });
});
