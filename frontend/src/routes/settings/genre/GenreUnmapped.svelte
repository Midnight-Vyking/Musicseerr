<script lang="ts">
	import { genreUnmappedQuery, genreTaxonomyQuery, genreAutoMapQuery } from '$lib/queries/tags/TagQueries.svelte';
	import { API } from '$lib/constants';
	import { api } from '$lib/api/client';
	import { genreMappingsQuery } from '$lib/queries/tags/TagQueries.svelte';
	import { Lightbulb, Map, EyeOff } from 'lucide-svelte';
	import type { GenreAutoMapEntry, GenreTaxonomyCategory } from '$lib/types';

	const unmappedQuery = genreUnmappedQuery();
	const taxonomyQuery = genreTaxonomyQuery();
	const mappingsQuery = genreMappingsQuery();

	const allCanonicals = $derived(
		(taxonomyQuery.data?.categories ?? []).flatMap(
			(c: GenreTaxonomyCategory) => c.genres
		).filter((g: string, i: number, a: string[]) => a.indexOf(g) === i).sort()
	);

	// Per-row state
	let selectedCanonical = $state<Record<string, string>>({});
	let mappingStatus = $state<Record<string, 'idle' | 'saving' | 'ignoring' | 'error' | 'done'>>({});
	let mappingErrors = $state<Record<string, string>>({});
	let suggestionsOpen = $state<Record<string, boolean>>({});

	// Auto-map: all unmapped at once
	let autoMapResults = $state<Record<string, GenreAutoMapEntry> | null>(null);
	let autoMapLoading = $state(false);
	let autoMapError = $state('');

	async function loadSuggestions() {
		const unmapped = unmappedQuery.data ?? [];
		if (unmapped.length === 0) return;
		autoMapLoading = true;
		autoMapError = '';
		try {
			const results = await api.global.post<GenreAutoMapEntry[]>(API.genre.autoMap(), {
				genres: unmapped
			});
			const map: Record<string, GenreAutoMapEntry> = {};
			for (const entry of results) {
				map[entry.raw_genre] = entry;
			}
			autoMapResults = map;
		} catch (e: unknown) {
			autoMapError = e instanceof Error ? e.message : 'Failed to get suggestions';
		} finally {
			autoMapLoading = false;
		}
	}

	function getSuggestionCount(raw: string): number {
		if (!autoMapResults) return 0;
		return autoMapResults[raw]?.suggestions?.length ?? 0;
	}

	function getTopSuggestion(raw: string): string | null {
		if (!autoMapResults) return null;
		const entry = autoMapResults[raw];
		if (!entry?.suggestions?.length) return null;
		return entry.suggestions[0].canonical;
	}

	function toggleSuggestions(raw: string) {
		suggestionsOpen = { ...suggestionsOpen, [raw]: !suggestionsOpen[raw] };
	}

	async function mapGenre(raw: string) {
		const canonical = selectedCanonical[raw] ?? getTopSuggestion(raw);
		if (!canonical) return;
		mappingStatus = { ...mappingStatus, [raw]: 'saving' };
		mappingErrors = { ...mappingErrors, [raw]: '' };
		try {
			await api.global.post(API.genre.mappings(), {
				raw_genre: raw,
				canonical_genre: canonical
			});
			mappingStatus = { ...mappingStatus, [raw]: 'done' };
			unmappedQuery.refetch();
			mappingsQuery.refetch();
		} catch (e: unknown) {
			mappingStatus = { ...mappingStatus, [raw]: 'error' };
			mappingErrors = { ...mappingErrors, [raw]: e instanceof Error ? e.message : 'Failed' };
		}
	}

	async function ignoreGenre(raw: string) {
		mappingStatus = { ...mappingStatus, [raw]: 'ignoring' };
		try {
			await api.global.post(API.genre.mappings(), {
				raw_genre: raw,
				canonical_genre: '__ignored__'
			});
			mappingStatus = { ...mappingStatus, [raw]: 'done' };
			unmappedQuery.refetch();
			mappingsQuery.refetch();
		} catch (e: unknown) {
			mappingStatus = { ...mappingStatus, [raw]: 'error' };
			mappingErrors = { ...mappingErrors, [raw]: e instanceof Error ? e.message : 'Failed' };
		}
	}

	function setCanonical(raw: string, value: string) {
		selectedCanonical = { ...selectedCanonical, [raw]: value };
	}
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<p class="text-sm text-base-content/60">
			Raw genres from your library that haven't been mapped to a canonical genre yet.
		</p>
		<button
			class="btn btn-sm btn-outline"
			onclick={loadSuggestions}
			disabled={autoMapLoading || (unmappedQuery.data?.length ?? 0) === 0}
		>
			{#if autoMapLoading}
				<span class="loading loading-spinner loading-xs"></span>
			{/if}
			<Lightbulb class="h-4 w-4" />
			Get Suggestions
		</button>
	</div>

	{#if autoMapError}
		<div class="alert alert-error"><span>{autoMapError}</span></div>
	{/if}

	{#if unmappedQuery.isPending}
		<div class="flex items-center gap-2 text-sm text-base-content/50 py-8">
			<span class="loading loading-spinner loading-sm"></span>
			Loading unmapped genres...
		</div>
	{:else if unmappedQuery.error}
		<div class="alert alert-error">
			<span>{unmappedQuery.error instanceof Error ? unmappedQuery.error.message : 'Failed to load unmapped genres'}</span>
		</div>
	{:else if !unmappedQuery.data || unmappedQuery.data.length === 0}
		<div class="alert alert-success">
			<span>All genres are mapped! No unmapped genres found.</span>
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="table table-zebra table-sm">
				<thead>
					<tr>
						<th>Raw Genre</th>
						<th>Suggested Canonical</th>
						<th>Canonical Picker</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each unmappedQuery.data as raw (raw)}
						{#if mappingStatus[raw] === 'done'}
							<tr class="opacity-50">
								<td class="line-through">{raw}</td>
								<td colspan="3" class="text-success text-sm">Mapped ✓</td>
							</tr>
						{:else}
							<tr>
								<td class="font-medium">{raw}</td>
								<td>
									{#if getTopSuggestion(raw)}
										<div>
											<span class="badge badge-info">{getTopSuggestion(raw)}</span>
											{#if getSuggestionCount(raw) > 1}
												<button
													class="btn btn-xs btn-ghost ml-1"
													onclick={() => toggleSuggestions(raw)}
												>
													+{getSuggestionCount(raw) - 1} more
												</button>
											{/if}
										</div>
										{#if suggestionsOpen[raw] && autoMapResults?.[raw]?.suggestions}
											<div class="mt-1 space-y-0.5">
												{#each autoMapResults[raw].suggestions.slice(1) as s}
													<span class="badge badge-ghost text-xs">{s.canonical} ({s.score}%)</span>
												{/each}
											</div>
										{/if}
									{:else if autoMapResults && !autoMapResults[raw]}
										<span class="text-xs text-base-content/40">No suggestion</span>
									{/if}
								</td>
								<td>
									<select
										class="select select-bordered select-xs w-full max-w-[160px]"
										value={selectedCanonical[raw] ?? getTopSuggestion(raw) ?? ''}
										onchange={(e: Event) => {
											const target = e.target as HTMLSelectElement;
											setCanonical(raw, target.value);
										}}
									>
										<option value="">Pick genre...</option>
										{#each allCanonicals as g}
											<option value={g}>{g}</option>
										{/each}
									</select>
								</td>
								<td>
									<div class="flex gap-1">
										<button
											class="btn btn-xs btn-primary"
											onclick={() => mapGenre(raw)}
											disabled={mappingStatus[raw] === 'saving' ||
												(!selectedCanonical[raw] && !getTopSuggestion(raw))}
										>
											{#if mappingStatus[raw] === 'saving'}
												<span class="loading loading-spinner loading-xs"></span>
											{/if}
											<Map class="h-3 w-3" />
											Map
										</button>
										<button
											class="btn btn-xs btn-ghost text-warning"
											onclick={() => ignoreGenre(raw)}
											disabled={mappingStatus[raw] === 'saving' || mappingStatus[raw] === 'ignoring'}
										>
											{#if mappingStatus[raw] === 'ignoring'}
												<span class="loading loading-spinner loading-xs"></span>
											{/if}
											<EyeOff class="h-3 w-3" />
											Ignore
										</button>
									</div>
									{#if mappingStatus[raw] === 'error'}
										<span class="text-xs text-error block mt-1">{mappingErrors[raw]}</span>
									{/if}
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
