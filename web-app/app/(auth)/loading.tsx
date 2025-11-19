import { SkeletonPanel } from '@/components/ui/states/SkeletonPanel';

export default function AuthLoading() {
  return (
    <div className="mx-auto w-full max-w-md">
      <SkeletonPanel lines={6} />
    </div>
  );
}
