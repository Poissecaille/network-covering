import type { CoverageEntry } from "../api/coverageClient";
import { isCoverageError } from "../api/coverageClient";

type CoverageResultsProps = {
  result: CoverageEntry | null;
  error: string | null;
};

export function CoverageResults({ result, error }: CoverageResultsProps) {
  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!result) {
    return null;
  }

  if (isCoverageError(result)) {
    return <p className="error">{result.error}</p>;
  }

  return (
    <div className="results">
      {Object.entries(result).map(([operator, coverage]) => (
        <div key={operator} className="operator">
          <h3>{operator}</h3>
          <ul>
            {Object.entries(coverage).map(([technology, isCovered]) => (
              <li key={technology}>
                {technology}:{" "}
                <span className={isCovered ? "status-ok" : "status-ko"}>
                  {isCovered ? "OK" : "KO"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
