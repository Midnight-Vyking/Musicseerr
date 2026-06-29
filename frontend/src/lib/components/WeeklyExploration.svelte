<script lang="ts">
	import type { WeeklyExplorationSection as SectionType } from '$lib/types';
	import { Sparkles, ExternalLink } from 'lucide-svelte';
	import HorizontalCarousel from './HorizontalCarousel.svelte';
	import WeeklyExplorationCard from './WeeklyExplorationCard.svelte';

	interface Props {
		section: SectionType;
	}

	let { section }: Props = $props();

	function formatPlaylistDate(dateStr: string): string {
		try {
			const d = new Date(dateStr);
			return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
		} catch {
			return '';
		}
	}

	const formattedDate = $derived(formatPlaylistDate(section.playlist_date));
</script>

<section class="my-10">
	<div class="mb-4">
		<div class="flex items-center justify-between gap-3">
			<div class="flex items-center gap-2 sm:gap-3 flex-wrap min-w-0">
				<div class="flex items-center gap-2">
					<Sparkles class="h-5 w-5 text-warning shrink-0" />
					<h2 class="text-lg font-bold text-base-content">Weekly Exploration</h2>
				</div>
				{#if formattedDate}
					<span class="hidden sm:inline text-xs text-base-content/40 whitespace-nowrap">
						{formattedDate}
					</span>
				{/if}
			</div>

			{#if section.source_url}
				<a
					href={section.source_url}
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-1 text-xs text-base-content/40
						hover:text-primary transition-colors shrink-0"
					title="View on ListenBrainz"
				>
					ListenBrainz
					<ExternalLink class="h-3 w-3" />
				</a>
			{/if}
		</div>

		{#if formattedDate}
			<span class="sm:hidden text-xs text-base-content/40">
				{formattedDate}
			</span>
		{/if}
	</div>

	<HorizontalCarousel>
		{#each section.tracks as track (track.artist_name + track.title)}
			<WeeklyExplorationCard {track} />
		{/each}
	</HorizontalCarousel>
</section>
