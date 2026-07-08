<script lang="ts">
	import { Check, Loader2, Pencil, X } from 'lucide-svelte';
	import GenrePicker from './GenrePicker.svelte';
	import { previewBatchTags, applyBatchTags } from '$lib/queries/tags/TagMutations.svelte';
	import { toastStore } from '$lib/stores/toast';
	import type {
		LibraryFileMeta,
		TrackTagEntry,
		BatchTagPreviewItem,
		BatchTagUpdateResponse
	} from '$lib/types';

	interface Props {
		tracks: LibraryFileMeta[];
		releaseGroupMbid: string;
		open: boolean;
		onClose?: () => void;
	}

	let { tracks, releaseGroupMbid, open = $bindable(false), onClose }: Props = $props();

	// Lazily initialized mutations (only when component is rendered)
	let _previewMut: ReturnType<typeof previewBatchTags> | null = $state(null);
	let _applyMut: ReturnType<typeof applyBatchTags> | null = $state(null);

	$effect(() => {
		if (open) {
			_previewMut = previewBatchTags();
			_applyMut = applyBatchTags();
		}
	});

	// Form state - only set fields you want to change (null = leave unchanged)
	let title = $state<string>('');
	let artist = $state<string>('');
	let album = $state<string>('');
	let albumArtist = $state<string>('');
	let year = $state<string>('');
	let genre = $state<string>('');
	let trackNumber = $state<string>('');
	let discNumber = $state<string>('');

	// Preview state
	let previewing = $state(false);
	let previewData = $state<BatchTagPreviewItem[]>([]);
	let applying = $state(false);
	let result = $state<BatchTagUpdateResponse | null>(null);

	let dialogEl = $state<HTMLDialogElement | null>(null);

	$effect(() => {
		if (open) {
			dialogEl?.showModal();
		} else {
			dialogEl?.close();
			reset();
		}
	});

	function reset() {
		title = artist = album = albumArtist = year = genre = trackNumber = discNumber = '';
		previewData = [];
		previewing = false;
		applying = false;
		result = null;
		_previewMut?.reset();
		_applyMut?.reset();
	}

	function close() {
		open = false;
		onClose?.();
	}

	function hasAnyChange(): boolean {
		return !!(title || artist || album || albumArtist || year || genre || trackNumber || discNumber);
	}

	function buildEntries(): TrackTagEntry[] {
		return tracks.map((t) => ({
			file_id: t.id,
			title: title || null,
			artist: artist || null,
			album: album || null,
			album_artist: albumArtist || null,
			year: year ? parseInt(year, 10) : null,
			genre: genre || null,
			track_number: trackNumber ? parseInt(trackNumber, 10) : null,
			disc_number: discNumber ? parseInt(discNumber, 10) : null
		}));
	}

	async function handlePreview() {
		if (!hasAnyChange() || !_previewMut) return;
		previewing = true;
		previewData = [];
		try {
			const res = await _previewMut.mutateAsync({ tags: buildEntries() });
			previewData = res.items;
		} catch (e) {
			toastStore.show({
				message: e instanceof Error ? e.message : 'Preview failed',
				type: 'error'
			});
		} finally {
			previewing = false;
		}
	}

	async function handleApply() {
		if (!hasAnyChange() || !_applyMut) return;
		applying = true;
		result = null;
		try {
			const res = await _applyMut.mutateAsync({ tags: buildEntries() });
			result = res;
			if (res.failed === 0) {
				toastStore.show({
					message: `${res.updated} track(s) updated`,
					type: 'success'
				});
				setTimeout(close, 800);
			} else {
				toastStore.show({
					message: `${res.updated} updated, ${res.failed} failed`,
					type: 'info'
				});
			}
		} catch (e) {
			toastStore.show({
				message: e instanceof Error ? e.message : 'Batch update failed',
				type: 'error'
			});
		} finally {
			applying = false;
		}
	}
</script>

<dialog bind:this={dialogEl} class="modal modal-bottom sm:modal-middle" onclose={close}>
	<div class="modal-box max-w-xl">
		<h3 class="text-lg font-bold">
			Edit tags — {tracks.length} track{tracks.length !== 1 ? 's' : ''} selected
		</h3>
		<p class="text-xs text-base-content/50 mt-1">
			Leave a field blank to keep its current value. Only filled fields are changed.
		</p>

		<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
			<label class="form-control sm:col-span-2">
				<span class="label-text text-xs">Title</span>
				<input class="input input-bordered input-sm" bind:value={title} />
			</label>
			<label class="form-control">
				<span class="label-text text-xs">Artist</span>
				<input class="input input-bordered input-sm" bind:value={artist} />
			</label>
			<label class="form-control">
				<span class="label-text text-xs">Album artist</span>
				<input class="input input-bordered input-sm" bind:value={albumArtist} />
			</label>
			<label class="form-control sm:col-span-2">
				<span class="label-text text-xs">Album</span>
				<input class="input input-bordered input-sm" bind:value={album} />
			</label>
			<label class="form-control">
				<span class="label-text text-xs">Year</span>
				<input type="number" class="input input-bordered input-sm" bind:value={year} />
			</label>
			<label class="form-control">
				<span class="label-text text-xs">Genre</span>
				<GenrePicker value={genre || null} onSelect={(g) => (genre = g)} />
			</label>
			<label class="form-control">
				<span class="label-text text-xs">Track #</span>
				<input type="number" class="input input-bordered input-sm" bind:value={trackNumber} />
			</label>
			<label class="form-control">
				<span class="label-text text-xs">Disc #</span>
				<input type="number" class="input input-bordered input-sm" bind:value={discNumber} />
			</label>
		</div>

		<!-- Preview section -->
		{#if previewData.length > 0}
			<div class="mt-4">
				<div class="flex items-center gap-2 mb-2">
					<Check class="h-4 w-4 text-success" />
					<span class="text-sm font-medium">Changes preview</span>
				</div>
				<div class="bg-base-200 rounded-box max-h-48 overflow-y-auto">
					{#each previewData as item (item.file_id)}
						<div class="px-3 py-2 border-b border-base-300 last:border-b-0">
							<div class="text-xs font-medium truncate">{item.title}</div>
							<div class="text-[11px] text-base-content/50 truncate">{item.file_path}</div>
							{#each item.diffs as diff (diff.field)}
								<div class="mt-0.5 flex items-baseline gap-1.5 text-[11px]">
									<span class="text-base-content/50 w-16 shrink-0">{diff.field}:</span>
									{#if diff.old_value != null}
										<span class="text-error/70 line-through truncate">{diff.old_value}</span>
									{:else}
										<span class="text-base-content/30 italic">(empty)</span>
									{/if}
									<span class="text-base-content/30">→</span>
									{#if diff.new_value != null}
										<span class="text-success font-medium truncate">{diff.new_value}</span>
									{:else}
										<span class="text-base-content/30 italic">(empty)</span>
									{/if}
								</div>
							{/each}
							{#if item.diffs.length === 0}
								<div class="text-[11px] text-base-content/30 italic">No changes</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Result summary -->
		{#if result}
			<div class="mt-3 p-2 rounded text-xs {result.failed === 0 ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}">
				{result.updated} updated{#if result.failed > 0}, {result.failed} failed{/if}
				{#each result.errors as err (err.file_id)}
					<div class="text-error text-[10px] mt-0.5">
						<span class="font-mono">{err.file_id}:</span> {err.error}
					</div>
				{/each}
			</div>
		{/if}

		<div class="modal-action">
			<button class="btn btn-ghost btn-sm" onclick={close}>Cancel</button>
			<button
				class="btn btn-outline btn-sm"
				onclick={handlePreview}
				disabled={!hasAnyChange() || previewing || applying}
			>
				{#if previewing}
					<Loader2 class="h-4 w-4 animate-spin" />
				{/if}
				Preview
			</button>
			<button
				class="btn btn-primary btn-sm"
				onclick={handleApply}
				disabled={!hasAnyChange() || applying || _previewMut?.isPending}
			>
				{#if applying}
					<Loader2 class="h-4 w-4 animate-spin" />
				{/if}
				Apply to {tracks.length} track{tracks.length !== 1 ? 's' : ''}
			</button>
		</div>
	</div>
	<form method="dialog" class="modal-backdrop">
		<button onclick={close}>close</button>
	</form>
</dialog>
