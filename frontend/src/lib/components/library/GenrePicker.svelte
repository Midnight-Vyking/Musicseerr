<script lang="ts">
	import { Check, ChevronDown, Search, X } from 'lucide-svelte';
	import { genreTaxonomyQuery } from '$lib/queries/tags/TagQueries.svelte';
	import type { GenreTaxonomyCategory } from '$lib/types';

	interface Props {
		value: string | null;
		onSelect: (genre: string) => void;
	}

	let { value, onSelect }: Props = $props();

	// Lazily create taxonomy query only when dropdown opens
	let _loaded = $state(false);
	$effect(() => {
		if (open && !_loaded) _loaded = true;
	});

	// Create query only if needed (Svelte 5 reactivity guards against unused)
	const taxonomy = $derived.by(() => {
		if (!_loaded) return null;
		return genreTaxonomyQuery();
	});

	let open = $state(false);
	let search = $state('');
	let expandedCategory = $state<string | null>(null);

	let allGenres = $derived(
		taxonomy?.data?.categories?.flatMap((c: GenreTaxonomyCategory) => c.genres).filter(
			(g, i, a) => a.indexOf(g) === i
		).sort() ?? []
	);

	let filteredGenres = $derived(
		search
			? allGenres.filter((g) => g.toLowerCase().includes(search.toLowerCase()))
			: allGenres
	);

	function toggleDropdown(e: MouseEvent) {
		e.stopPropagation();
		open = !open;
		search = '';
		expandedCategory = null;
	}

	function selectGenre(genre: string) {
		onSelect(genre);
		open = false;
		search = '';
	}

	function toggleCategory(name: string) {
		expandedCategory = expandedCategory === name ? null : name;
	}

	function handleEscape(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			open = false;
			search = '';
		}
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="relative" onkeydown={handleEscape}>
	<button
		type="button"
		class="input input-bordered input-sm flex items-center gap-2 text-left w-full"
		onclick={toggleDropdown}
	>
		<span class={value ? 'flex-1 truncate' : 'flex-1 text-base-content/50'}>
			{value ?? 'Select genre...'}
		</span>
		{#if value}
			<div
				class="btn btn-ghost btn-xs btn-circle -mr-1"
				role="button"
				tabindex="0"
				onclick={(e) => {
					e.stopPropagation();
					onSelect('');
				}}
				onkeydown={(e) => {
					if (e.key === 'Enter' || e.key === ' ') {
						e.stopPropagation();
						onSelect('');
					}
				}}
			>
				<X class="h-3 w-3" />
			</div>
		{/if}
		<ChevronDown class="h-3.5 w-3.5 opacity-50 {open ? 'rotate-180' : ''}" />
	</button>

	{#if open}
		<div class="absolute z-50 mt-1 w-full bg-base-100 border border-base-300 rounded-box shadow-lg max-h-72 flex flex-col">
			<!-- Search -->
			<div class="p-2 border-b border-base-300">
				<label class="input input-sm input-bordered flex items-center gap-2">
					<Search class="h-3.5 w-3.5 opacity-50" />
					<input
						type="text"
						class="grow"
						placeholder="Search genres..."
						bind:value={search}
					/>
				</label>
			</div>

			<!-- Results -->
			<div class="overflow-y-auto flex-1">
				{#if search}
					<!-- Search results: flat list of matching genres -->
					{#each filteredGenres as genre (genre)}
						<button
							type="button"
							class="w-full text-left px-3 py-1.5 text-sm hover:bg-base-200 flex items-center gap-2 {genre === value ? 'bg-primary/10 font-medium' : ''}"
							onclick={() => selectGenre(genre)}
						>
							<span class="flex-1">{genre}</span>
							{#if genre === value}
								<Check class="h-3.5 w-3.5 text-primary" />
							{/if}
						</button>
					{:else}
						<div class="px-3 py-2 text-sm text-base-content/50">No genres found</div>
					{/each}
				{:else if taxonomy?.isPending}
					<div class="px-3 py-4 text-sm text-base-content/50 text-center">
						<span class="loading loading-spinner loading-xs"></span>
						Loading taxonomy...
					</div>
				{:else if taxonomy?.data?.categories}
					<!-- Category accordion -->
					{#if taxonomy}
						{#each taxonomy.data.categories as cat (cat.name)}
							{@const hasValue = cat.genres.includes(value ?? '')}
							<button
								type="button"
								class="w-full text-left px-3 py-1.5 text-sm font-medium hover:bg-base-200 flex items-center justify-between {hasValue ? 'bg-primary/10' : ''}"
								onclick={() => toggleCategory(cat.name)}
							>
								<span>
									{cat.name}
									<span class="ml-1 text-xs text-base-content/40">({cat.genres.length})</span>
								</span>
								<ChevronDown class="h-3 w-3 opacity-50 transition-transform {expandedCategory === cat.name ? 'rotate-180' : ''}" />
							</button>
							{#if expandedCategory === cat.name}
								{#each cat.genres as genre (genre)}
									<button
										type="button"
										class="w-full text-left pl-8 pr-3 py-1 text-sm hover:bg-base-200 flex items-center gap-2 {genre === value ? 'bg-primary/10 font-medium' : ''}"
										onclick={() => selectGenre(genre)}
									>
										<span class="flex-1">{genre}</span>
										{#if genre === value}
											<Check class="h-3.5 w-3.5 text-primary" />
										{/if}
									</button>
								{/each}
							{/if}
						{/each}
					{/if}
				{/if}
			</div>
		</div>

		<!-- Backdrop to close -->
		{#if open}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<div class="fixed inset-0 z-40" onclick={() => (open = false)} role="presentation"></div>
		{/if}
	{/if}
</div>
