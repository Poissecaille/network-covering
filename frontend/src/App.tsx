import { useState } from "react";
import { AddressForm } from "./components/AddressForm";
import { CoverageResults } from "./components/CoverageResults";
import { getCoverage, CoverageApiError } from "./api/coverageClient";
import type { CoverageEntry } from "./api/coverageClient";
import "./App.css";

function App() {
  const [result, setResult] = useState<CoverageEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSearch(address: string) {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const coverage = await getCoverage(address);
      setResult(coverage);
    } catch (err) {
      if (err instanceof CoverageApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main>
      <h1>Couverture réseau</h1>
      <AddressForm onSubmit={handleSearch} isLoading={isLoading} />
      <CoverageResults result={result} error={error} />
    </main>
  );
}

export default App;
