<script lang="ts">
	import GenreMappings from './GenreMappings.svelte';
	import GenreUnmapped from './GenreUnmapped.svelte';
	import GenreTaxonomy from './GenreTaxonomy.svelte';
	import GenreStats from './GenreStats.svelte';

	let tab = $state<'mappings' | 'unmapped' | 'taxonomy' | 'stats'>('unmapped');
</script>

<svelte:head><title>Genre Management · DroppedNeedle</title></svelte:head>

<div class="space-y-6">
	<h1 class="text-2xl font-bold">Genre Management</h1>

	<div role="tablist" class="tabs tabs-boxed">
		<button
			role="tab"
			class="tab"
			class:tab-active={tab === 'unmapped'}
			onclick={() => (tab = 'unmapped')}>Unmapped</button
		>
		<button
			role="tab"
			class="tab"
			class:tab-active={tab === 'mappings'}
			onclick={() => (tab = 'mappings')}>Mappings</button
		>
		<button
			role="tab"
			class="tab"
			class:tab-active={tab === 'taxonomy'}
			onclick={() => (tab = 'taxonomy')}>Taxonomy</button
		>
		<button
			role="tab"
			class="tab"
			class:tab-active={tab === 'stats'}
			onclick={() => (tab = 'stats')}>Stats</button
		>
	</div>

	{#if tab === 'unmapped'}
		<GenreUnmapped />
	{:else if tab === 'mappings'}
		<GenreMappings />
	{:else if tab === 'taxonomy'}
		<GenreTaxonomy />
	{:else if tab === 'stats'}
		<GenreStats />
	{/if}
</div>
