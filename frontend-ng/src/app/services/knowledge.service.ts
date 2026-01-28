import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';

/**
 * KnowledgeService - API client for Inception backend.
 * 
 * Connects to Python FastAPI backend at localhost:8000.
 * Provides typed access to entities, claims, stats, and learning data.
 */

export interface Stats {
    entities: number;
    claims: number;
    procedures: number;
    gaps: number;
    sources: number;
}

export interface Entity {
    id: string;
    name: string;
    type: string;
    confidence: number;
    created_at?: string;
}

export interface Claim {
    id: string;
    entity_id: string;
    text: string;
    source_id: string;
    confidence: number;
    created_at?: string;
}

export interface LearningStats {
    dapo: {
        entropy: number;
        kl_divergence: number;
    };
    grpo: {
        group_size: number;
        advantage_mean: number;
    };
    rlvr: {
        verification_rate: number;
        total_verified: number;
    };
    total_steps: number;
    buffer_size: number;
}

export interface RecentActivity {
    id: string;
    type: 'entity' | 'claim' | 'source' | 'gap';
    name: string;
    action: string;
    timestamp: string;
}

@Injectable({
    providedIn: 'root'
})
export class KnowledgeService {
    private readonly http = inject(HttpClient);
    private readonly baseUrl = 'http://127.0.0.1:8000';

    /**
     * Get system statistics (entity/claim/gap counts)
     */
    getStats(): Observable<Stats> {
        return this.http.get<Stats>(`${this.baseUrl}/api/stats`).pipe(
            catchError(err => {
                console.error('Failed to fetch stats:', err);
                return of({ entities: 0, claims: 0, procedures: 0, gaps: 0, sources: 0 });
            })
        );
    }

    /**
     * Get all entities with optional filtering
     */
    getEntities(limit?: number): Observable<Entity[]> {
        const params = limit ? `?limit=${limit}` : '';
        return this.http.get<Entity[]>(`${this.baseUrl}/api/entities${params}`).pipe(
            catchError(err => {
                console.error('Failed to fetch entities:', err);
                return of([]);
            })
        );
    }

    /**
     * Get all claims
     */
    getClaims(): Observable<Claim[]> {
        return this.http.get<Claim[]>(`${this.baseUrl}/api/claims`).pipe(
            catchError(err => {
                console.error('Failed to fetch claims:', err);
                return of([]);
            })
        );
    }

    /**
     * Get learning engine statistics
     */
    getLearningStats(): Observable<LearningStats | null> {
        return this.http.get<LearningStats>(`${this.baseUrl}/api/learning/stats`).pipe(
            catchError(err => {
                console.error('Failed to fetch learning stats:', err);
                return of(null);
            })
        );
    }

    /**
     * Get recent activity from the system
     * Returns recent entities as a proxy for activity
     */
    getRecentActivity(limit: number = 5): Observable<Entity[]> {
        return this.http.get<Entity[]>(`${this.baseUrl}/api/entities`).pipe(
            catchError(() => of([]))
        );
    }

    /**
     * Start ingestion from URL
     */
    ingest(url: string): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/ingest`, { url });
    }

    /**
     * Check API health
     */
    healthCheck(): Observable<{ status: string }> {
        return this.http.get<{ status: string }>(`${this.baseUrl}/health`).pipe(
            catchError(() => of({ status: 'unhealthy' }))
        );
    }
}
