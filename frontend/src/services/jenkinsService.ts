import { api } from "./api";
import type { JenkinsJob, ListResponse } from "@/types";

export async function fetchJenkinsJobs(): Promise<ListResponse<JenkinsJob>> {
  const { data } = await api.get<ListResponse<JenkinsJob>>("/jenkins/jobs");
  return data;
}

export async function fetchFailedJenkinsBuilds(): Promise<ListResponse<JenkinsJob>> {
  const { data } = await api.get<ListResponse<JenkinsJob>>("/jenkins/failed");
  return data;
}
