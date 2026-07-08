<script lang="ts">
	import { genreTaxonomyQuery } from '$lib/queries/tags/TagQueries.svelte';
	import { ChevronDown } from 'lucide-svelte';
	import type { GenreTaxonomyCategory } from '$lib/types';

	const taxonomyQuery = genreTaxonomyQuery();

	let expanded = $state<string | null>(null);
	let filter = $state('');

	function toggle(name: string) {
		expanded = expanded === name ? null : name;
	}

	const filteredCategories = $derived(
		filter
			? (taxonomyQuery.data?.categories ?? []).filter(
					(c: GenreTaxonomyCategory) =>
						c.name.toLowerCase().includes(filter.toLowerCase()) ||
						c.genres.some((g: string) => g.toLowerCase().includes(filter.toLowerCase()))
				)
			: (taxonomyQuery.data?.categories ?? [])
	);

	let totalGenres = $derived(
		(taxonomyQuery.data?.categories ?? []).reduce(
			(sum: number, c: GenreTaxonomyCategory) => sum + c.genres.length,
			0
		)
	);
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<div>
			<p class="text-sm text-base-content/60">
				Complete genre taxonomy — {taxonomyQuery.data?.categories?.length ?? 0} categories,
				{totalGenres} genres.
			</p>
		</div>
		<div class="form-control max-w-xs">
			<label class="input input-sm input-bordered flex items-center gap-2">
				<input type="text" class="grow" placeholder="Filter taxonomy..." bind:value={filter} />
			</label>
		</div>
	</div>

	{#if taxonomyQuery.isPending}
		<div class="flex items-center gap-2 text-sm text-base-content/50 py-8">
			<span class="loading loading-spinner loading-sm"></span>
			Loading taxonomy...
		</div>
	{:else if taxonomyQuery.error}
		<div class="alert alert-error">
			<span>{taxonomyQuery.error instanceof Error ? taxonomyQuery.error.message : 'Failed to load taxonomy'}</span>
		</div>
	{:else}
		<div class="space-y-1">
			{#each filteredCategories as cat (cat.name)}
				<div class="border border-base-300 rounded-box">
					<button
						class="flex items-center justify-between w-full px-4 py-3 text-left font-medium hover:bg-base-200 transition-colors rounded-box"
						class:rounded-b-none={expanded === cat.name}
						onclick={() => toggle(cat.name)}
					>
						<div class="flex items-center gap-2">
							<span>{cat.name}</span>
							<span class="badge badge-sm">{cat.genres.length}</span>
						</div>
						<ChevronDown
							class="h-4 w-4 transition-transform {expanded === cat.name ? 'rotate-180' : ''}"
						/>
					</button>
					{#if expanded === cat.name}
						<div class="px-4 pb-3">
							<div class="flex flex-wrap gap-1.5">
								{#each cat.genres as genre (genre)}
									<span class="badge badge-outline">{genre}</span>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			{:else}
				<div class="text-center text-base-content/50 py-8">
					No categories match "{filter}".
				</div>
			{/each}
		</div>
	{/if}
</div>
