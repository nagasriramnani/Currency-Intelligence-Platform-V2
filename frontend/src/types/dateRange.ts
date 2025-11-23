export type DateRangePreset = '1Y' | '3Y' | '5Y' | 'MAX' | 'CUSTOM';

export interface DateRangeState {
  preset: DateRangePreset;
  startDate: string | null;
  endDate: string | null;
}


