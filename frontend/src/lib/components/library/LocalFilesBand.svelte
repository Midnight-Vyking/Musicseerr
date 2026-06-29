<script lang="ts">
	import { Headphones, ArrowRight } from 'lucide-svelte';
	import { getLocalStatsQuery, getLocalRecentQuery } from '$lib/queries/local/LocalQueries.svelte';
	import { getCoverUrl } from '$lib/utils/errorHandling';

	const statsQuery = getLocalStatsQuery();
	const recentQuery = getLocalRecentQuery();
	const stats = $derived(statsQuery.data);
	const collage = $derived((recentQuery.data ?? []).slice(0, 8));
</script>

<section
	class="group relative isolate overflow-hidden rounded-3xl border border-base-content/10 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:border-base-content/20 hover:shadow-2xl"
>
	{#if collage.length}
		<div aria-hidden="true" class="pointer-events-none absolute inset-0 flex scale-110 blur-2xl">
			{#each collage as album (album.musicbrainz_id)}
				<img
					src={getCoverUrl(album.cover_url, album.musicbrainz_id)}
					alt=""
					loading="lazy"
					class="h-full min-w-0 flex-1 object-cover opacity-60"
				/>
			{/each}
		</div>
	{/if}

	<div
		aria-hidden="true"
		class="absolute inset-0"
		style="background:
			linear-gradient(105deg, oklch(from var(--color-base-100) l c h / 0.96) 28%, oklch(from var(--color-base-100) l c h / 0.72) 62%, rgb(var(--brand-localfiles) / 0.22) 100%);"
	></div>
	<div
		aria-hidden="true"
		class="pointer-events-none absolute -top-16 -right-12 h-56 w-56 rounded-full blur-3xl"
		style="background: rgb(var(--brand-localfiles) / 0.28);"
	></div>
	<div
		aria-hidden="true"
		class="pointer-events-none absolute inset-0 opacity-[0.05]"
		style="background-image: url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%224%22 stitchTiles=%22stitch%22/></filter><rect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23n)%22 opacity=%220.5%22/></svg>'); background-size: 200px;"
	></div>

	<!-- stretched link under the content so empty area navigates, while playback buttons (pointer-events re-enabled) still act in place; avoids nested interactives -->
	<a
		href="/library/local"
		aria-label="Enter the Listening Room"
		class="absolute inset-0 z-10 rounded-3xl focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-base-100 focus-visible:outline-none"
		style="--tw-ring-color: rgb(var(--brand-localfiles));"
	></a>

	<div class="pointer-events-none relative z-20 flex flex-col gap-5 p-6 sm:p-8">
		<div class="flex items-start justify-between gap-3">
			<div class="flex items-center gap-4">
				<div
					class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ring-1 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110"
					style="background: rgb(var(--brand-localfiles) / 0.15); color: rgb(var(--brand-localfiles)); --tw-ring-color: rgb(var(--brand-localfiles) / 0.35);"
				>
					<Headphones class="h-7 w-7" />
				</div>
				<div>
					<h2 class="text-xl font-black tracking-tight sm:text-2xl">Local Files</h2>
					<p class="text-sm text-base-content/60">
						{#if stats}
							{stats.total_tracks.toLocaleString()} tracks · {stats.total_artists.toLocaleString()} artists
							· {stats.total_size_human}
						{:else}
							Your local music collection
						{/if}
					</p>
				</div>
			</div>
			<div
				class="flex shrink-0 items-center gap-2 text-right"
				style="color: rgb(var(--brand-localfiles));"
			>
				<div class="leading-tight">
					<div
						class="hidden text-[10px] font-semibold tracking-[0.2em] uppercase opacity-70 sm:block"
					>
						Enter the
					</div>
					<div class="text-sm font-black tracking-tight sm:text-base">Listening Room</div>
				</div>
				<ArrowRight class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
			</div>
		</div>

		<div class="h-px w-full bg-base-content/10"></div>

		<a
			href="/library/local"
			class="flex items-center justify-between pointer-events-auto rounded-xl px-1 py-1 -mx-1 hover:bg-base-content/5 transition-colors"
		>
			<span class="text-sm font-semibold" style="color: rgb(var(--brand-localfiles));"
				>Open Listening Room</span
			>
			<ArrowRight class="h-4 w-4" style="color: rgb(var(--brand-localfiles));" />
		</a>
	</div>
</section>
