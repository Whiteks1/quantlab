import "../styles.css";
import AppLegacyShell from "../components/App.jsx";

/**
 * App - Canonical React runtime entrypoint for Vite/Production.
 *
 * Instead of being a parallel placeholder, this component now delegates
 * to the functional shell in components/App.jsx. This unifies the
 * workstation experience while maintaining state ownership in React.
 */
export default function App() {
  return <AppLegacyShell />;
}
