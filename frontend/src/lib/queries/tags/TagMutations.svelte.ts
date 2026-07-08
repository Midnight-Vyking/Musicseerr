import { createMutation } from '@tanstack/svelte-query';
import { API } from '$lib/constants';
import { api } from '$lib/api/client';
import { invalidateQueriesWithPersister } from '../QueryClient';
import type {
	BatchTagPreviewResponse,
	BatchTagUpdateRequest,
	BatchTagUpdateResponse
} from '$lib/types';

export function previewBatchTags() {
	return createMutation(() => ({
		mutationFn: (input: BatchTagUpdateRequest) =>
			api.global.post<BatchTagPreviewResponse>(API.library.batchTagPreview(), input)
	}));
}

export function applyBatchTags() {
	return createMutation(() => ({
		mutationFn: (input: BatchTagUpdateRequest) =>
			api.global.post<BatchTagUpdateResponse>(API.library.batchTagUpdate(), input)
	}));
}
