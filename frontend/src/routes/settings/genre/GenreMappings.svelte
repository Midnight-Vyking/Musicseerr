<script lang="ts">
	import { genreMappingsQuery, genreTaxonomyQuery } from '$lib/queries/tags/TagQueries.svelte';
	import { API } from '$lib/constants';
	import { api } from '$lib/api/client';
	import type { GenreMapping, GenreTaxonomyCategory } from '$lib/types';

	const mappingsQuery = genreMappingsQuery();
	const taxonomyQuery = genreTaxonomyQuery();

	let editingRaw = $state<string | null>(null);
	let editCanonical = $state('');
	let editError = $state('');
	let editSaving = $state(false);

	let filter = $state('');

	const allCanonicals = $derived(
		(taxonomyQuery.data?.categories ?? []).flatMap(
			(c: GenreTaxonomyCategory) => c.genres
		).filter((g: string, i: number, a: string[]) => a.indexOf(g) === i).sort()
	);

	const filteredMappings = $derived(
		filter
			? (mappingsQuery.data ?? []).filter(
					(m: GenreMapping) =>
						m.raw_genre.toLowerCase().includes(filter.toLowerCase()) ||
						m.canonical_genre.toLowerCase().includes(filter.toLowerCase())
				)
			: (mappingsQuery.data ?? [])
	);

	function startEdit(mapping: GenreMapping) {
		editingRaw = mapping.raw_genre;
		editCanonical = mapping.canonical_genre;
		editError = '';
	}

	function cancelEdit() {
		editingRaw = null;
		editCanonical = '';
		editError = '';
	}

	async function saveEdit() {
		if (!editingRaw || !editCanonical.trim()) return;
		editSaving = true;
		editError = '';
		try {
			await api.global.post(API.genre.mappings(), {
				raw_genre: editingRaw,
				canonical_genre: editCanonical.trim()
			});
			mappingsQuery.refetch();
			cancelEdit();
		} catch (e: unknown) {
			editError = e instanceof Error ? e.message : 'Failed to save mapping';
		} finally {
			editSaving = false;
		}
	}
</script>

<div class="space-y-4">
	<p class="text-sm text-base-content/60">
		All raw-to-canonical genre mappings. Click Edit to change a mapping.
	</p>

	<!-- Filter -->
	<div class="form-control max-w-xs">
		<label class="input input-sm input-bordered flex items-center gap-2">
			<input type="text" class="grow" placeholder="Filter mappings..." bind:value={filter} />
		</label>
	</div>

	{#if mappingsQuery.isPending}
		<div class="flex items-center gap-2 text-sm text-base-content/50 py-8">
			<span class="loading loading-spinner loading-sm"></span>
			Loading mappings...
		</div>
	{:else if mappingsQuery.error}
		<div class="alert alert-error">
			<span>{mappingsQuery.error instanceof Error ? mappingsQuery.error.message : 'Failed to load mappings'}</span>
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="table table-zebra table-sm">
				<thead>
					<tr>
						<th>Raw Genre</th>
						<th>Canonical Genre</th>
						<th>Confidence</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each filteredMappings as mapping (mapping.raw_genre)}
						{#if editingRaw === mapping.raw_genre}
							<tr>
								<td class="font-medium">{mapping.raw_genre}</td>
								<td>
									<select
										class="select select-bordered select-sm w-full max-w-xs"
										bind:value={editCanonical}
									>
										<option value="">Select canonical...</option>
										{#each allCanonicals as g}
											<option value={g}>{g}</option>
										{/each}
									</select>
								</td>
								<td>{mapping.confidence}</td>
								<td>
									<div class="flex gap-1">
										<button
											class="btn btn-sm btn-primary"
											onclick={saveEdit}
											disabled={editSaving || !editCanonical.trim()}
										>
											{#if editSaving}
												<span class="loading loading-spinner loading-xs"></span>
											{/if}
											Save
										</button>
										<button class="btn btn-sm btn-ghost" onclick={cancelEdit}>Cancel</button>
									</div>
								</td>
							</tr>
						{:else}
							<tr>
								<td class="font-medium">{mapping.raw_genre}</td>
								<td><span class="badge badge-outline">{mapping.canonical_genre}</span></td>
								<td>
									<span
										class="badge {mapping.confidence >= 80
											? 'badge-success'
											: mapping.confidence >= 50
												? 'badge-warning'
												: 'badge-ghost'}"
									>
										{mapping.confidence}
									</span>
								</td>
								<td>
									<button class="btn btn-xs btn-ghost" onclick={() => startEdit(mapping)}>
										Edit
									</button>
								</td>
							</tr>
						{/if}
					{:else}
						<tr>
							<td colspan="4" class="text-center text-base-content/50 py-4">
								{#if filter}
									No mappings match "{filter}".
								{:else}
									No mappings found.
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	{#if editError}
		<div class="alert alert-error"><span>{editError}</span></div>
	{/if}
</div>
