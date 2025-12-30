
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import "./index.css";

// Apply saved theme before React mounts to avoid a flash of the default theme.
try {
  const theme = localStorage.getItem("theme");
  if (theme === "pink") {
    document.documentElement.setAttribute("data-theme", "pink");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
} catch {
  // ignore
}

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
  
