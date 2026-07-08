import { createQuery } from '@tanstack/svelte-query';
import { API } from '$lib/constants';
import { api } from '$lib/api/client';
import type {
	GenreMapping,
	GenreAutoMapEntry,
	GenreTaxonomyCategory,
	GenreStatsEntry
} from '$lib/types';

export function genreMappingsQuery() {
	return createQuery(() => ({
		queryKey: ['genre', 'mappings'],
		queryFn: () => api.global.get<GenreMapping[]>(API.genre.mappings())
	}));
}

export function genreUnmappedQuery() {
	return createQuery(() => ({
		queryKey: ['genre', 'unmapped'],
		queryFn: () => api.global.get<string[]>(API.genre.unmapped())
	}));
}

export function genreTaxonomyQuery() {
	return createQuery(() => ({
		queryKey: ['genre', 'taxonomy'],
		queryFn: () => api.global.get<{ categories: GenreTaxonomyCategory[] }>(API.genre.taxonomy()),
		staleTime: 1000 * 60 * 60 // 1 hour - taxonomy rarely changes
	}));
}

export function genreStatsQuery() {
	return createQuery(() => ({
		queryKey: ['genre', 'stats'],
		queryFn: () => api.global.get<GenreStatsEntry[]>(API.genre.stats())
	}));
}

export function genreAutoMapQuery(rawGenres: string[]) {
	return createQuery(() => ({
		queryKey: ['genre', 'auto-map', ...rawGenres],
		queryFn: () => api.global.post<GenreAutoMapEntry[]>(API.genre.autoMap(), { genres: rawGenres }),
		enabled: rawGenres.length > 0
	}));
}
