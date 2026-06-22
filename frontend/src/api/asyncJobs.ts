import { api } from "./client";
import { ItineraryResponse } from "../types";

type JobAccepted = { job_id: string; status: string };
type JobStatus = {
  job_id: string;
  status: string;
  result?: ItineraryResponse;
  error?: string;
};

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function requestItinerary(payload: Record<string, unknown>): Promise<ItineraryResponse> {
  const response = await api.post<ItineraryResponse | JobAccepted>("/ai/itinerary", payload);

  if (response.status === 202 && "job_id" in response.data) {
    const jobId = response.data.job_id;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      await sleep(2000);
      const statusResponse = await api.get<JobStatus>(`/ai/jobs/${jobId}`);
      if (statusResponse.data.status === "completed" && statusResponse.data.result) {
        return statusResponse.data.result;
      }
      if (statusResponse.data.status === "failed") {
        throw new Error(statusResponse.data.error || "Itinerary generation failed");
      }
    }
    throw new Error("Itinerary generation timed out");
  }

  return response.data as ItineraryResponse;
}

export async function requestCompare(payload: Record<string, unknown>) {
  const response = await api.post("/ai/compare", payload);
  if (response.status === 202 && "job_id" in response.data) {
    const jobId = response.data.job_id as string;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      await sleep(2000);
      const statusResponse = await api.get(`/ai/jobs/${jobId}`);
      if (statusResponse.data.status === "completed") {
        return statusResponse.data.result;
      }
      if (statusResponse.data.status === "failed") {
        throw new Error(statusResponse.data.error || "Comparison failed");
      }
    }
    throw new Error("Comparison timed out");
  }
  return response.data;
}
