import 'package:flutter/material.dart';
import 'skeleton.dart';

class ListSkeleton extends StatelessWidget {
  final int itemCount;
  final bool withCard;

  const ListSkeleton({super.key, this.itemCount = 6, this.withCard = false});

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      physics: const NeverScrollableScrollPhysics(),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (_, __) =>
          withCard ? const _SkeletonCardItem() : const _SkeletonTileItem(),
    );
  }
}

class _SkeletonTileItem extends StatelessWidget {
  const _SkeletonTileItem();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          const SkeletonBox(width: 40, height: 40, borderRadius: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                SkeletonLine(height: 14),
                SizedBox(height: 6),
                SkeletonLine(width: 120, height: 12),
              ],
            ),
          ),
          const SizedBox(width: 12),
          const SkeletonBox(width: 60, height: 14),
        ],
      ),
    );
  }
}

class _SkeletonCardItem extends StatelessWidget {
  const _SkeletonCardItem();

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SkeletonBox(width: 36, height: 36, borderRadius: 18),
                const SizedBox(width: 12),
                const Expanded(child: SkeletonLine(height: 14)),
                const SizedBox(width: 12),
                const SkeletonBox(width: 50, height: 14),
              ],
            ),
            const SizedBox(height: 14),
            const SkeletonBox(height: 8, borderRadius: 4),
          ],
        ),
      ),
    );
  }
}
