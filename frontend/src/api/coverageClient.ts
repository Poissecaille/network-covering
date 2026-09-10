const API_BASE_URL = "http://localhost:8000";

export type TechnologyCoverage = {
  "2G": boolean;
  "3G": boolean;
  "4G": boolean;
};

export type OperatorCoverage = Record<string, TechnologyCoverage>;

export type CoverageEntry = OperatorCoverage | { error: string };

export function isCoverageError(
  entry: CoverageEntry,
): entry is { error: string } {
  return "error" in entry;
}

export class CoverageApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "CoverageApiError";
    this.status = status;
  }
}

export async function getCoverage(address: string): Promise<CoverageEntry> {
  const queryId = crypto.randomUUID();

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/coverage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [queryId]: address }),
    });
  } catch {
    throw new CoverageApiError("Unable to reach the server.", 0);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? "A server error occurred.";
    throw new CoverageApiError(message, response.status);
  }

  const data = await response.json();
  return data[queryId] as CoverageEntry;
}
