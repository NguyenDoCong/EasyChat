(function () {
    async function fetchOverlayData(url = window.location.href) {
        try {
            console.log('Fetching data for:', url);

            const response = await fetch("http://127.0.0.1:8000/crawl", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ href: url })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Loaded content for:', url);
            } else {
                console.error('API returned status:', response.status);
            }
        } catch (err) {
            console.error("Error fetching data for", url, err);
        }
    }
    fetchOverlayData();
})();