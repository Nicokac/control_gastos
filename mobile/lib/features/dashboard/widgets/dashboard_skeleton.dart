import 'package:flutter/material.dart';
import '../../../core/widgets/skeleton.dart';

class DashboardSkeleton extends StatelessWidget {
  const DashboardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      physics: const NeverScrollableScrollPhysics(),
      children: [
        // Month selector
        const Center(child: SkeletonBox(width: 160, height: 20)),
        const SizedBox(height: 20),

        // Balance card
        Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SkeletonLine(width: 60, height: 14),
                const SizedBox(height: 10),
                const SkeletonLine(width: 140, height: 32),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: SkeletonBox(height: 56, borderRadius: 12)),
                    const SizedBox(width: 12),
                    Expanded(child: SkeletonBox(height: 56, borderRadius: 12)),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Quick actions row
        Row(
          children: [
            Expanded(child: SkeletonBox(height: 40, borderRadius: 12)),
            const SizedBox(width: 8),
            Expanded(child: SkeletonBox(height: 40, borderRadius: 12)),
          ],
        ),
        const SizedBox(height: 12),

        // Pending recurring card
        Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const SkeletonBox(width: 20, height: 20, borderRadius: 4),
                    const SizedBox(width: 8),
                    const SkeletonLine(width: 120, height: 16),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    const SkeletonBox(width: 80, height: 24, borderRadius: 20),
                    const SizedBox(width: 8),
                    const SkeletonBox(width: 100, height: 24, borderRadius: 20),
                  ],
                ),
                const SizedBox(height: 10),
                const SkeletonBox(height: 6, borderRadius: 4),
                const SizedBox(height: 12),
                const SkeletonLine(height: 16),
                const SizedBox(height: 8),
                const SkeletonLine(height: 16),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Chart card
        Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SkeletonLine(width: 160, height: 16),
                const SizedBox(height: 16),
                Row(
                  children: [
                    const SkeletonBox(
                        width: 120, height: 120, borderRadius: 60),
                    const SizedBox(width: 20),
                    Expanded(
                      child: Column(
                        children: [
                          const SkeletonLine(height: 12),
                          const SizedBox(height: 8),
                          const SkeletonLine(height: 12),
                          const SizedBox(height: 8),
                          SkeletonLine(width: 80, height: 12),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Recent transactions card
        Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SkeletonLine(width: 160, height: 16),
                const SizedBox(height: 12),
                ...List.generate(
                  4,
                  (_) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      children: [
                        const SkeletonBox(
                            width: 36, height: 36, borderRadius: 18),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SkeletonLine(height: 12),
                              const SizedBox(height: 4),
                              SkeletonLine(width: 80, height: 10),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        const SkeletonBox(width: 60, height: 14),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
