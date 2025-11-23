/**
 * Alerts Panel Component
 * Displays recent Slack alert history
 */

import React from 'react';
import { Bell, AlertTriangle, TrendingUp, Activity, Zap, CheckCircle, XCircle } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import type { AlertHistory } from '@/lib/api';
import { SkeletonBlock } from '@/components/SkeletonBlock';

interface AlertsPanelProps {
  alerts: AlertHistory[];
  isLoading?: boolean;
  onTestAlert?: () => void;
  testAlertLoading?: boolean;
  onSendSummary?: () => void;
  sendSummaryLoading?: boolean;
  summaryStatus?: 'success' | 'error';
}

export function AlertsPanel({
  alerts,
  isLoading,
  onTestAlert,
  testAlertLoading,
  onSendSummary,
  sendSummaryLoading,
  summaryStatus,
}: AlertsPanelProps) {
  const getAlertIcon = (triggerType: string) => {
    switch (triggerType) {
      case 'YoY Movement':
        return <TrendingUp className="h-4 w-4" />;
      case 'Volatility Spike':
        return <Activity className="h-4 w-4" />;
      case 'Anomaly Detected':
        return <AlertTriangle className="h-4 w-4" />;
      case 'Forecast Deviation':
        return <Zap className="h-4 w-4" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  };

  const getAlertColor = (triggerType: string) => {
    switch (triggerType) {
      case 'YoY Movement':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'Volatility Spike':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'Anomaly Detected':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'Forecast Deviation':
        return 'bg-violet-500/10 text-violet-400 border-violet-500/20';
      default:
        return 'bg-sapphire-500/10 text-sapphire-400 border-sapphire-500/20';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 h-full">
      <div className="flex flex-col gap-6 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-sapphire-400" />
            <h3 className="text-lg font-bold text-white">Recent Alerts</h3>
          </div>
          {summaryStatus === 'success' && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
              <CheckCircle className="h-3 w-3" /> Sent to Slack
            </span>
          )}
          {summaryStatus === 'error' && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-rose-400 bg-rose-500/10 px-2 py-1 rounded-full border border-rose-500/20">
              <XCircle className="h-3 w-3" /> Failed to send
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          {onTestAlert && (
            <button
              onClick={onTestAlert}
              disabled={testAlertLoading}
              className="flex-1 rounded-lg border border-sapphire-700/50 bg-sapphire-900/30 px-4 py-2 text-sm font-semibold text-sapphire-300 hover:bg-sapphire-800/50 hover:text-white disabled:opacity-50 transition-all"
            >
              {testAlertLoading ? 'Sending…' : 'Test Alert'}
            </button>
          )}

          {onSendSummary && (
            <button
              onClick={onSendSummary}
              disabled={sendSummaryLoading}
              className="flex-[2] rounded-lg bg-sapphire-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sapphire-500 disabled:opacity-50 transition-all shadow-lg shadow-sapphire-600/20"
            >
              {sendSummaryLoading ? 'Posting…' : 'Send Summary to Slack'}
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <SkeletonBlock key={i} className="h-20 bg-sapphire-800/50" />
          ))}
        </div>
      ) : !alerts || alerts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-sapphire-700/30 bg-sapphire-900/20 px-4 py-12 text-center text-sm text-sapphire-400">
          <Bell className="h-8 w-8 mx-auto mb-3 text-sapphire-600 opacity-50" />
          Alerts will appear here as soon as conditions are triggered.
        </div>
      ) : (
        <div className="space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
          {alerts.map((alert, index) => (
            <div
              key={index}
              className="group rounded-xl border border-sapphire-800/50 bg-sapphire-900/30 px-4 py-3 transition-all hover:border-sapphire-700/50 hover:bg-sapphire-800/30"
            >
              <div className="flex items-start gap-3">
                <div
                  className={`mt-0.5 rounded-lg p-2 border ${getAlertColor(alert.trigger_type)}`}
                >
                  {getAlertIcon(alert.trigger_type)}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h4 className="text-sm font-semibold text-white group-hover:text-sapphire-100 transition-colors">
                      {alert.trigger_type}
                    </h4>
                    <span className="text-xs text-sapphire-400 font-mono">
                      {formatDate(alert.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-sapphire-300 mt-0.5">{alert.currency}</p>

                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    {Object.entries(alert.details).map(([key, value]) => (
                      <span
                        key={key}
                        className="rounded-md bg-sapphire-950/50 border border-sapphire-800/50 px-2 py-1 text-sapphire-300"
                      >
                        <strong className="uppercase tracking-wide text-sapphire-500 text-[10px] mr-1">
                          {key.replace(/_/g, ' ')}:
                        </strong>{' '}
                        {typeof value === 'number' ? value.toFixed(2) : String(value)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

