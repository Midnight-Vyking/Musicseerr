<script lang="ts">
	import { Library, ArrowRight, Sparkles, AlertTriangle, RefreshCw } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import { fromStore } from 'svelte/store';
	import { integrationStore } from '$lib/stores/integration';
	import { authStore } from '$lib/stores/authStore.svelte';
	import { getLocalStatsQuery } from '$lib/queries/local/LocalQueries.svelte';
	import { getLibraryStatsQuery } from '$lib/queries/library/LibraryQueries.svelte';
	import { formatLastUpdated } from '$lib/utils/formatting';
	import type { FormatInfo } from '$lib/types';

	interface Props {
		loading?: boolean;
		refreshing?: boolean;
		lastUpdated?: Date | null;
		onRefresh?: () => void;
	}

	let { loading = false, refreshing = false, lastUpdated = null, onRefresh }: Props = $props();

	type CardState = 'loading' | 'prompt' | 'error' | 'stats';

	const integrations = fromStore(integrationStore);
	const localEnabled = $derived(integrations.current.localfiles);

	const localStatsQuery = getLocalStatsQuery(() => localEnabled);
	const libraryStatsQuery = getLibraryStatsQuery();

	const localStats = $derived(localStatsQuery.data);
	const libraryStats = $derived(libraryStatsQuery.data);

	function topFormats(breakdown: Record<string, FormatInfo>): string {
		return Object.entries(breakdown)
			.sort((a, b) => b[1].count - a[1].count)
			.slice(0, 2)
			.map(([format]) => format.toUpperCase())
			.join(' · ');
	}
	const localFormats = $derived(localStats ? topFormats(localStats.format_breakdown) : '');

	const totalTracks = $derived((libraryStats?.total_tracks ?? localStats?.total_tracks ?? 0).toLocaleString());
	const totalArtists = $derived((libraryStats?.total_artists ?? localStats?.total_artists ?? 0).toLocaleString());
	const totalAlbums = $derived((libraryStats?.total_albums ?? localStats?.total_albums ?? 0).toLocaleString());
	const localSize = $derived(localStats?.total_size_human ?? '');
	const libUnmatched = $derived(libraryStats?.unmatched_count ?? 0);
	const libLastScan = $derived(
		libraryStats?.last_scan_at ? new Date(libraryStats.last_scan_at * 1000) : null
	);

	const hasAnyStats = $derived(totalTracks !== '0' || totalAlbums !== '0');

	const cardState = $derived<CardState>(
		!integrations.current.loaded || loading
			? 'loading'
			: libraryStats || localStats
				? 'stats'
				: libraryStatsQuery.isError || localStatsQuery.isError
					? 'error'
					: hasAnyStats
						? 'stats'
						: 'prompt'
	);

	const stats = $derived([
		{ value: totalTracks, label: 'tracks' },
		{ value: totalArtists, label: 'artists' },
		{ value: totalAlbums, label: 'albums' }
	]);

	const footerLines = $derived.by(() => {
		const parts: string[] = [];
		if (localSize) parts.push(localSize);
		if (localFormats) parts.push(localFormats);
		if (libLastScan && !libUnmatched) parts.push(`Scanned ${formatLastUpdated(libLastScan)}`);
		return parts.join(' · ');
	});

	const footerText = $derived(
		libUnmatched > 0
			? `${libUnmatched} album${libUnmatched === 1 ? '' : 's'} need review`
			: footerLines || 'Not scanned yet'
	);

	const promptText = $derived(
		authStore.isAdmin
			? 'Add a library path and run a scan to fill your library.'
			: 'Your library is being prepared by an admin.'
	);
</script>

<div class="discover-section-enter">
	<div
		role="link"
		tabindex="0"
		onclick={(e) => { const t = e.target as HTMLElement; if (!t.closest('button')) goto('/library'); }}
		onkeydown={(e) => { if (e.key === 'Enter') goto('/library'); }}
		class="group block relative overflow-hidden bg-gradient-to-br from-primary/20 via-info/10 to-base-200 border-b border-base-content/5 transition-colors duration-300 hover:from-primary/25 hover:via-info/12 hover:to-base-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary cursor-pointer"
	>
		<div
			aria-hidden="true"
			class="pointer-events-none absolute inset-0 opacity-[0.04]"
			style="background-image: url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%224%22 stitchTiles=%22stitch%22/></filter><rect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23n)%22 opacity=%220.5%22/></svg>'); background-size: 200px;"
		></div>
		<div
			aria-hidden="true"
			class="pointer-events-none absolute -top-12 -right-12 h-44 w-44 rounded-full bg-primary/25 blur-3xl transition-transform duration-500 group-hover:scale-125"
		></div>

		<div class="relative flex flex-col gap-3 px-4 py-4 sm:gap-4 sm:px-6 sm:py-5 lg:px-8">
			<!-- Header row -->
			<div class="flex items-start justify-between gap-2">
				<div class="flex items-center gap-3 min-w-0">
					<div
						class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/30 sm:h-12 sm:w-12 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110"
					>
						<Library class="h-5 w-5 text-primary sm:h-6 sm:w-6" />
					</div>
					<div class="min-w-0">
						<h1 class="text-lg font-bold leading-tight sm:text-xl">Your Library</h1>
						<p class="text-xs text-base-content/50 sm:text-sm">
							{hasAnyStats ? `${totalTracks} tracks · ${totalArtists} artists · ${totalAlbums} albums` : 'Browse, scan & organise'}
						</p>
					</div>
				</div>

				<div class="flex items-center gap-2 shrink-0">
					{#if refreshing}
						<span class="loading loading-spinner loading-xs text-primary/60"></span>
					{:else if lastUpdated && !loading}
						<span class="hidden text-[10px] text-base-content/40 sm:inline">Updated {formatLastUpdated(lastUpdated)}</span>
					{/if}
					{#if onRefresh}
						<button
							type="button"
							class="btn btn-ghost btn-sm btn-circle"
							onclick={(e) => { e.preventDefault(); e.stopPropagation(); onRefresh(); }}
							disabled={refreshing || loading}
							aria-label="Refresh library stats"
						>
							<RefreshCw class="h-4 w-4 {refreshing ? 'animate-spin' : ''}" />
						</button>
					{/if}
					<ArrowRight
						class="h-5 w-5 shrink-0 text-base-content/40 transition-transform duration-300 group-hover:translate-x-1 group-hover:text-primary"
					/>
				</div>
			</div>

			{#if cardState === 'loading'}
				<div class="flex gap-4 sm:gap-8">
					{#each Array(3) as _, i (i)}
						<div class="space-y-1">
							<div class="skeleton h-5 w-10 rounded sm:h-6 sm:w-12"></div>
							<div class="skeleton h-2 w-8 rounded"></div>
						</div>
					{/each}
				</div>
				<div class="skeleton h-3 w-40 rounded"></div>
			{:else if cardState === 'stats'}
				<div class="flex gap-4 sm:gap-8">
					{#each stats as stat (stat.label)}
						<div class="min-w-0">
							<div class="truncate text-xl font-extrabold tabular-nums sm:text-2xl">
								{stat.value}
							</div>
							<div class="text-[10px] font-medium tracking-wide text-base-content/50 uppercase sm:text-[11px]">
								{stat.label}
							</div>
						</div>
					{/each}
				</div>
				<div class="flex items-center justify-between gap-2 border-t border-base-content/10 pt-2.5 sm:pt-3">
					{#if libUnmatched > 0}
						<button
							type="button"
							class="min-w-0 truncate text-xs text-warning hover:text-warning/80 hover:underline transition-colors"
							onclick={(e) => { e.stopPropagation(); goto('/library/unmatched'); }}
						>
							Review {libUnmatched} album{libUnmatched === 1 ? '' : 's'}
						</button>
					{:else}
						<span class="min-w-0 truncate text-xs text-base-content/50">
							{footerText}
						</span>
					{/if}
					<span class="shrink-0 text-xs font-semibold text-primary">Open Library</span>
				</div>
			{:else}
				{@const isError = cardState === 'error'}
				<div
					class="flex items-center gap-2 rounded-xl px-3 py-2 text-xs sm:text-sm {isError
						? 'bg-warning/10 text-warning'
						: 'bg-base-100/40 text-base-content/70'}"
				>
					{#if isError}
						<AlertTriangle class="h-4 w-4 shrink-0" />
						<span>Couldn't load stats — open to retry.</span>
					{:else}
						<Sparkles class="h-4 w-4 shrink-0 text-primary" />
						<span>{promptText}</span>
					{/if}
				</div>
				<div class="flex justify-end border-t border-base-content/10 pt-2.5 sm:pt-3">
					<span class="text-xs font-semibold text-primary">Open Library</span>
				</div>
			{/if}
		</div>
	</div>
</div>
