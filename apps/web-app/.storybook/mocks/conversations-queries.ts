import { conversationDetailFixture } from '../../components/shared/conversations/__stories__/fixtures';

type DetailMode = 'loading' | 'error' | 'loaded';

let detailMode: DetailMode = 'loaded';

export const setConversationDetailMode = (mode: DetailMode) => {
  detailMode = mode;
};

export function useConversationDetail(conversationId: string | null) {
  if (!conversationId) {
    return {
      conversationHistory: null,
      isLoadingDetail: false,
      isFetchingDetail: false,
      detailError: null,
      refetchDetail: async () => {},
    };
  }

  if (detailMode === 'loading') {
    return {
      conversationHistory: null,
      isLoadingDetail: true,
      isFetchingDetail: false,
      detailError: null,
      refetchDetail: async () => {},
    };
  }

  if (detailMode === 'error') {
    return {
      conversationHistory: null,
      isLoadingDetail: false,
      isFetchingDetail: false,
      detailError: 'Failed to load conversation.',
      refetchDetail: async () => {},
    };
  }

  return {
    conversationHistory: conversationDetailFixture,
    isLoadingDetail: false,
    isFetchingDetail: false,
    detailError: null,
    refetchDetail: async () => {},
  };
}
