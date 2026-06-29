<script lang="ts">
	import { Play, Shuffle, Sparkles } from 'lucide-svelte';
	import { getLocalStatsQuery } from '$lib/queries/local/LocalQueries.svelte';
	import { createLibraryTrackLoader } from '$lib/utils/libraryTrackLoader.svelte';
	import { buildDiscoveryQueueFromLocal } from '$lib/player/queueHelpers';
	import { playerStore } from '$lib/stores/player.svelte';
	import { playbackToast } from '$lib/stores/playbackToast.svelte';
	import { API } from '$lib/constants';
	import { api } from '$lib/api/client';
	import type { NativeTrackListItem, NativeTrackPage } from '$lib/types';

	const statsQuery = getLocalStatsQuery();
	const stats = $derived(statsQuery.data);

	const PAGE_SIZE = 100;
	const loader = createLibraryTrackLoader<NativeTrackListItem>(
		{
			fetchPageUrl: (limit, offset) => API.library.tracks(limit, offset, 'recent'),
			buildQueue: (tracks) => buildDiscoveryQueueFromLocal(tracks),
			pageSize: PAGE_SIZE
		},
		(items) => playerStore.appendQueueSilent(items),
		(items, startIndex, shuffle) => playerStore.playQueue(items, startIndex, shuffle),
		() => playerStore.regenerateShuffleOrder(),
		(message, type) => playbackToast.show(message, type)
	);

	let busy = $state<'' | 'play' | 'shuffle' | 'surprise'>('');

	function firstPage(): Promise<NativeTrackPage> {
		return api.global.get<NativeTrackPage>(API.library.tracks(PAGE_SIZE, 0, 'recent'));
	}

	async function playAll() {
		if (busy) return;
		busy = 'play';
		try {
			const page = await firstPage();
			if (!page.items.length) {
				playbackToast.show('No tracks to play yet', 'info');
				return;
			}
			loader.playAll(page.items, page.total);
		} catch {
			playbackToast.show("Couldn't start playback", 'error');
		} finally {
			busy = '';
		}
	}

	async function shuffleAll() {
		if (busy) return;
		busy = 'shuffle';
		try {
			const page = await firstPage();
			if (!page.items.length) {
				playbackToast.show('No tracks to play yet', 'info');
				return;
			}
			loader.shuffleAll(page.items, page.total);
		} catch {
			playbackToast.show("Couldn't start playback", 'error');
		} finally {
			busy = '';
		}
	}

	async function surprise() {
		if (busy) return;
		busy = 'surprise';
		try {
			const count = stats?.total_tracks ?? 0;
			const offset = count > 0 ? Math.floor(Math.random() * count) : 0;
			const page = await api.global.get<NativeTrackPage>(API.library.tracks(1, offset, 'recent'));
			const track = page.items[0];
			if (!track) {
				playbackToast.show('Nothing to surprise you with yet', 'info');
				return;
			}
			playerStore.playQueue(buildDiscoveryQueueFromLocal([track]), 0, false);
		} catch {
			playbackToast.show("Couldn't pick a track", 'error');
		} finally {
			busy = '';
		}
	}
</script>

<div class="flex flex-col gap-3">
	{#if stats}
		<div class="flex items-center gap-2 text-sm">
			<span class="font-semibold" style="color: rgb(var(--brand-localfiles));">Local Files</span>
			<span class="text-base-content/50 text-xs">
				{stats.total_tracks.toLocaleString()} tracks · {stats.total_artists.toLocaleString()} artists · {stats.total_size_human}
			</span>
		</div>
	{/if}

	<div class="flex flex-wrap items-center gap-2 sm:gap-3">
	<button
		onclick={playAll}
		disabled={busy === 'play'}
		class="btn btn-sm sm:btn-md gap-1.5 border-0 text-base-100 shadow-lg transition-transform hover:scale-[1.02]"
		style="background: rgb(var(--brand-localfiles));"
	>
		{#if busy === 'play'}
			<span class="loading loading-spinner loading-xs"></span>
		{:else}
			<Play class="h-4 w-4" />
		{/if}
		Play All
	</button>
	<button
		onclick={shuffleAll}
		disabled={busy === 'shuffle'}
		class="btn btn-sm sm:btn-md gap-1.5 border bg-base-100/40 backdrop-blur-sm hover:bg-base-100/70"
		style="border-color: rgb(var(--brand-localfiles) / 0.4);"
	>
		{#if busy === 'shuffle'}
			<span class="loading loading-spinner loading-xs"></span>
		{:else}
			<Shuffle class="h-4 w-4" />
		{/if}
		Shuffle
	</button>
	<button
		onclick={surprise}
		disabled={busy === 'surprise'}
		class="btn btn-sm sm:btn-md btn-ghost gap-1.5"
	>
		{#if busy === 'surprise'}
			<span class="loading loading-spinner loading-xs"></span>
		{:else}
			<Sparkles class="h-4 w-4" />
		{/if}
		Surprise me
	</button>
	</div>
</div>
