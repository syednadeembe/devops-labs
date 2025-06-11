document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const labArea = document.getElementById("lab-area");
  const terminalFrame = document.getElementById("terminal-frame");

  function waitForTerminal(url, retries = 5, delay = 2000) {
    console.log("Checking terminal availability at:", url);
    fetch(url).then(res => {
      if (res.ok) {
        terminalFrame.src = url;
        loginForm.style.display = "none";
        labArea.style.display = "block";
      } else {
        if (retries > 0) {
          console.log(`Retrying in ${delay / 1000}s... (${retries} left)`);
          setTimeout(() => waitForTerminal(url, retries - 1, delay), delay);
        } else {
          alert("Terminal not ready yet. Please try again later.");
        }
      }
    }).catch(err => {
      if (retries > 0) {
        console.log(`Retry failed. Trying again... (${retries} left)`);
        setTimeout(() => waitForTerminal(url, retries - 1, delay), delay);
      } else {
        alert("Terminal failed to start.");
      }
    });
  }
  loginForm.style.display = "none";
  document.getElementById("loading").style.display = "block";
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const tokenResponse = await fetch("http://13.200.227.6:30080/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `username=${username}&password=${password}`,
      });

      const tokenData = await tokenResponse.json();

      if (!tokenResponse.ok || !tokenData.access_token) {
        alert("Login failed");
        return;
      }

      const token = tokenData.access_token;
      localStorage.setItem("access_token", token);

      const sessionResponse = await fetch("http://13.200.227.6:30081/api/lab-session", {
        method: "GET",
        headers: {
          "accept": "application/json",
          "Authorization": `Bearer ${token}`
        },
      });

      const sessionData = await sessionResponse.json();
      if (!sessionResponse.ok || !sessionData.message) {
        alert("Failed to start lab");
        return;
      }

      const sessionId = sessionData.message.split("session ID: ")[1];
      const labUrl = `http://13.200.227.6:30082/labs/${sessionId}`;

      waitForTerminal(labUrl);

    } catch (err) {
      console.error("Error:", err);
      alert("Something went wrong");
    }
  });
});
