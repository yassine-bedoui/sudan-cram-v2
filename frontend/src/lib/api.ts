// src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// ========= MATCH YOUR ACTUAL BACKEND RESPONSE =========
interface AnalyticsResponse {
  summary: {
    total_regions: number;
    avg_climate_risk: number;
    avg_conflict_risk: number;
    total_events: number;
    total_fatalities: number;
    highest_risk_region: string;
  };
  risk_distribution: {
    climate: Record<string, number>;
    conflict: Record<string, number>;
  };
  top_regions: Array<{
    region: string;
    climate_risk_score: number;
    political_risk_score: number;
    cdi_category: string;
    risk_category: string;
    events_6m: number;
    fatalities_6m: number;
  }>;
  regional_data: Array<{
    region: string;
    climate_risk_score: number;
    political_risk_score: number;
    events_6m: number;
    fatalities_6m: number;
  }>;
}

interface Region {
  region: string;
  climate_risk_score: number;
  cdi_category: string;
  political_risk_score: number;
  risk_category: string;
  bivariate_category: string;
  events_6m: number;
  fatalities_6m: number;
  trend: string;
}

interface RegionsResponse {
  regions: Region[];
  total_count: number;
  risk_summary: {
    climate: Record<string, number>;
    conflict: Record<string, number>;
  };
}

// ========= NEW: DASHBOARD INTERFACE =========
interface DashboardStats {
  summary: {
    conflict_events: number;
    states_analyzed: number;
    risk_assessments: number;
    data_confidence: number;
  };
  quick_insights: {
    highest_risk_state: string;
    active_alerts: number;
    alert_breakdown: {
      high: number;
      very_high: number;
      extreme: number;
    };
    trend: {
      direction: string;
      percentage: number;
    };
  };
  risk_distribution: {
    climate: Record<string, number>;
    conflict: Record<string, number>;
  };
  metrics: {
    total_events: number;
    total_fatalities: number;
    avg_climate_risk: number;
    avg_conflict_risk: number;
  };
}

class CRAMAPIService {
  private async fetchWithTimeout<T>(url: string, timeout = 10000): Promise<T> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        signal: controller.signal,
        cache: 'no-store',
      });
      clearTimeout(id);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(id);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  async getAnalytics(): Promise<AnalyticsResponse> {
    return this.fetchWithTimeout(`${API_BASE_URL}/api/analytics`);
  }

  async getRegions(): Promise<RegionsResponse> {
    return this.fetchWithTimeout(`${API_BASE_URL}/api/regions`);
  }

  // ========= NEW: DASHBOARD METHOD =========
  async getDashboardStats(): Promise<DashboardStats> {
    return this.fetchWithTimeout(`${API_BASE_URL}/api/dashboard`);
  }
}

export const cramAPI = new CRAMAPIService();
export type { AnalyticsResponse, Region, RegionsResponse, DashboardStats };
