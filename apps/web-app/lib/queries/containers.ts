import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  bindAgentToContainer,
  createContainer,
  deleteContainer,
  listContainers,
  unbindAgentFromContainer,
} from '@/lib/api/containers';
import type { ContainerCreateRequest } from '@/lib/api/client/types.gen';
import { queryKeys } from './keys';

export function useContainersQuery() {
  return useQuery({ queryKey: queryKeys.containers.list(), queryFn: listContainers });
}

export function useCreateContainer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ContainerCreateRequest) => createContainer(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.containers.list() }).catch(() => {});
    },
  });
}

export function useDeleteContainer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteContainer(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.containers.list() }).catch(() => {});
    },
  });
}

export function useBindAgentContainer(agentKey: string) {
  return useMutation({
    mutationFn: (containerId: string) => bindAgentToContainer(agentKey, { container_id: containerId }),
  });
}

export function useUnbindAgentContainer(agentKey: string) {
  return useMutation({ mutationFn: () => unbindAgentFromContainer(agentKey) });
}
