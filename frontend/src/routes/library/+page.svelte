<script lang="ts">
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LibraryDashboard from '$lib/components/library/LibraryDashboard.svelte';
	import LibraryQuickActions from '$lib/components/library/LibraryQuickActions.svelte';
	import { authStore } from '$lib/stores/authStore.svelte';
	import { Headphones, SlidersHorizontal, Waypoints, X, ArrowRight } from 'lucide-svelte';
	import { integrationStore } from '$lib/stores/integration';
	import { fromStore } from 'svelte/store';

	const integrations = fromStore(integrationStore);
	const localEnabled = $derived(integrations.current.localfiles);

	const CONNECT_APPS_HREF = '/settings?tab=connect-apps';
	const BANNER_KEY = 'droppedneedle_connect_apps_banner_dismissed';

	let bannerDismissed = $state(true); // assume dismissed until we read storage (no SSR flash)

	$effect(() => {
		if (typeof localStorage !== 'undefined') {
			bannerDismissed = localStorage.getItem(BANNER_KEY) === '1';
		}
	});

	function dismissBanner() {
		bannerDismissed = true;
		if (typeof localStorage !== 'undefined') {
			localStorage.setItem(BANNER_KEY, '1');
		}
	}

	function scrollToControls() {
		document
			.getElementById('library-controls')
			?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}
</script>

<svelte:head><title>Library · DroppedNeedle</title></svelte:head>

<div class="min-h-[calc(100vh-200px)]">
	<PageHeader subtitle="Your scanned music library">
		{#snippet title()}<span class="whitespace-nowrap">Library</span>{/snippet}
		{#snippet actions()}
			<div class="flex flex-wrap items-center gap-2 justify-end">
				{#if localEnabled}
					<a
						href="/library/local"
						class="group/drop group btn btn-sm gap-2 rounded-full border-0 text-base-100 shadow-lg transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl sm:btn-md"
						style="background: rgb(var(--brand-localfiles));"
					>
						<Headphones class="h-4 w-4 transition-transform duration-200 group-hover/drop:scale-110" />
						<span class="group-hover/drop:hidden text-xs font-semibold">Drop the Needle!</span>
						<span class="hidden group-hover/drop:inline text-xs">
							Enter the <span class="font-black">Listening Room</span>
						</span>
						<ArrowRight class="h-3.5 w-3.5 transition-transform group-hover/drop:translate-x-0.5" />
					</a>
				{/if}
				<a
					href={CONNECT_APPS_HREF}
					class="group btn btn-sm gap-2 rounded-full border border-base-content/15 bg-base-100/50 text-base-content backdrop-blur transition-all duration-200 hover:-translate-y-0.5 hover:border-accent/40 hover:bg-base-100/80 sm:btn-md"
				>
					<Waypoints class="h-4 w-4 transition-transform duration-200 group-hover:scale-110" />
					<span>Connect Apps</span>
				</a>
				{#if authStore.isAdmin}
					<button
						onclick={scrollToControls}
						class="group btn btn-sm gap-2 rounded-full border border-base-content/15 bg-base-100/50 text-base-content backdrop-blur transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:bg-base-100/80 sm:btn-md"
					>
						<SlidersHorizontal
							class="h-4 w-4 transition-transform duration-200 group-hover:rotate-12"
						/>
						<span>Controls</span>
					</button>
				{/if}
			</div>
		{/snippet}
	</PageHeader>
	<div class="space-y-8 px-4 pb-12 sm:space-y-12 sm:px-6 lg:px-8">
		{#if !bannerDismissed}
			<div
				class="flex items-center gap-3 rounded-box border border-accent/25 bg-base-200 p-4"
				role="note"
			>
				<Waypoints class="hidden h-6 w-6 shrink-0 text-accent sm:block" aria-hidden="true" />
				<div class="min-w-0 flex-1">
					<p class="font-semibold">Stream this library in your favourite app</p>
					<p class="text-sm text-base-content/60">
						Connect Symfonium, Finamp and more over the OpenSubsonic or Jellyfin protocols.
					</p>
				</div>
				<a href={CONNECT_APPS_HREF} class="btn btn-sm btn-accent">Set up</a>
				<button
					class="btn btn-ghost btn-sm btn-square"
					aria-label="Dismiss"
					onclick={dismissBanner}
				>
					<X class="h-4 w-4" aria-hidden="true" />
				</button>
			</div>
		{/if}
		{#if localEnabled}
			<LibraryQuickActions />
		{/if}
		<LibraryDashboard />
	</div>
</div>
