<script lang="ts">
	import { genreStatsQuery } from '$lib/queries/tags/TagQueries.svelte';
	import type { GenreStatsEntry } from '$lib/types';

	const statsQuery = genreStatsQuery();

	let maxCount = $derived(
		Math.max(1, ...(statsQuery.data ?? []).map((s: GenreStatsEntry) => s.track_count))
	);
</script>

<div class="space-y-4">
	<p class="text-sm text-base-content/60">
		Genre distribution across your library by track count.
	</p>

	{#if statsQuery.isPending}
		<div class="flex items-center gap-2 text-sm text-base-content/50 py-8">
			<span class="loading loading-spinner loading-sm"></span>
			Loading stats...
		</div>
	{:else if statsQuery.error}
		<div class="alert alert-error">
			<span>{statsQuery.error instanceof Error ? statsQuery.error.message : 'Failed to load stats'}</span>
		</div>
	{:else if !statsQuery.data || statsQuery.data.length === 0}
		<div class="alert">
			<span>No genre stats available. Scan your library first.</span>
		</div>
	{:else}
		<div class="card bg-base-200">
			<div class="card-body p-4">
				<h3 class="card-title text-sm">Track Count by Genre</h3>
				<div class="space-y-2">
					{#each statsQuery.data as entry (entry.canonical_genre)}
						<div class="flex items-center gap-3">
							<span class="text-sm w-40 truncate font-medium">{entry.canonical_genre}</span>
							<div class="flex-1">
								<progress
									class="progress progress-primary w-full"
									value={entry.track_count}
									max={maxCount}
								></progress>
							</div>
							<span class="text-sm tabular-nums w-16 text-right text-base-content/70">
								{entry.track_count}
							</span>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- Summary badges -->
		<div class="card bg-base-200">
			<div class="card-body p-4">
				<h3 class="card-title text-sm mb-2">Top Genres</h3>
				<div class="flex flex-wrap gap-2">
					{#each statsQuery.data.slice(0, 20) as entry (entry.canonical_genre)}
						<span class="badge badge-lg {entry.track_count >= maxCount * 0.5
							? 'badge-primary'
							: entry.track_count >= maxCount * 0.2
								? 'badge-secondary'
								: 'badge-outline'}">
							{entry.canonical_genre}
							<span class="ml-1 opacity-70">{entry.track_count}</span>
						</span>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>
