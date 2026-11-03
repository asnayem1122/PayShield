import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/presentation/login_screen.dart';
import '../features/auth/presentation/register_screen.dart';
import '../features/dashboard/presentation/dashboard_screen.dart';
import '../features/fraud_detection/presentation/risk_indicators_screen.dart';
import '../features/profile/presentation/profile_screen.dart';
import '../features/shell/presentation/main_shell_screen.dart';
import '../features/transactions/presentation/transaction_details_screen.dart';
import '../features/transactions/presentation/transaction_history_screen.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<NavigatorState> _shellNavigatorKey = GlobalKey<NavigatorState>();

final GoRouter appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/dashboard',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/register',
      builder: (context, state) => const RegisterScreen(),
    ),
    ShellRoute(
      navigatorKey: _shellNavigatorKey,
      builder: (context, state, child) {
        return MainShellScreen(child: child);
      },
      routes: [
        GoRoute(
          path: '/dashboard',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: DashboardScreen(),
          ),
        ),
        GoRoute(
          path: '/transactions',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: TransactionHistoryScreen(initialReviewOnly: false),
          ),
        ),
        GoRoute(
          path: '/review',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: TransactionHistoryScreen(initialReviewOnly: true),
          ),
        ),
        GoRoute(
          path: '/analytics',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: DashboardScreen(),
          ),
        ),
        GoRoute(
          path: '/profile',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: ProfileScreen(),
          ),
        ),
      ],
    ),
    GoRoute(
      path: '/transactions/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? '';
        return TransactionDetailsScreen(transactionId: id);
      },
    ),
    GoRoute(
      path: '/transactions/:id/risk',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? '';
        return RiskIndicatorsScreen(transactionId: id);
      },
    ),
  ],
);
