/**
 * Analysis Utility Functions
 * Mathematical helpers for correlation and seasonality calculations
 */

import { TimeSeriesDataPoint } from './api';

// Calculate mean of an array
export function calculateMean(data: number[]): number {
    if (data.length === 0) return 0;
    return data.reduce((sum, val) => sum + val, 0) / data.length;
}

// Calculate standard deviation
export function calculateStdDev(data: number[]): number {
    if (data.length < 2) return 0;
    const mean = calculateMean(data);
    const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (data.length - 1);
    return Math.sqrt(variance);
}

// Calculate covariance between two arrays
export function calculateCovariance(dataX: number[], dataY: number[]): number {
    if (dataX.length !== dataY.length || dataX.length < 2) return 0;
    const meanX = calculateMean(dataX);
    const meanY = calculateMean(dataY);

    let sum = 0;
    for (let i = 0; i < dataX.length; i++) {
        sum += (dataX[i] - meanX) * (dataY[i] - meanY);
    }
    return sum / (dataX.length - 1);
}

// Calculate Pearson correlation coefficient
export function calculateCorrelation(dataX: number[], dataY: number[]): number {
    const cov = calculateCovariance(dataX, dataY);
    const stdX = calculateStdDev(dataX);
    const stdY = calculateStdDev(dataY);

    if (stdX === 0 || stdY === 0) return 0;
    return cov / (stdX * stdY);
}

// Group data by currency for easier processing
export function groupDataByCurrency(data: TimeSeriesDataPoint[]): Record<string, TimeSeriesDataPoint[]> {
    return data.reduce((acc, point) => {
        if (!acc[point.currency]) {
            acc[point.currency] = [];
        }
        acc[point.currency].push(point);
        return acc;
    }, {} as Record<string, TimeSeriesDataPoint[]>);
}

// Align time series data by date to ensure we compare apples to apples
export function alignTimeSeries(
    dataA: TimeSeriesDataPoint[],
    dataB: TimeSeriesDataPoint[]
): { x: number[]; y: number[] } {
    const mapA = new Map(dataA.map(d => [d.record_date, d.exchange_rate]));
    const x: number[] = [];
    const y: number[] = [];

    dataB.forEach(d => {
        if (mapA.has(d.record_date)) {
            x.push(mapA.get(d.record_date)!);
            y.push(d.exchange_rate);
        }
    });

    return { x, y };
}

// Calculate seasonality (average return by month)
export function calculateSeasonality(data: TimeSeriesDataPoint[]): { month: string; avgReturn: number }[] {
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthReturns: Record<number, number[]> = {};

    data.forEach(point => {
        if (point.returns !== null) {
            const date = new Date(point.record_date);
            const month = date.getMonth();
            if (!monthReturns[month]) {
                monthReturns[month] = [];
            }
            monthReturns[month].push(point.returns);
        }
    });

    return monthNames.map((month, index) => ({
        month,
        avgReturn: monthReturns[index] ? calculateMean(monthReturns[index]) : 0
    }));
}
