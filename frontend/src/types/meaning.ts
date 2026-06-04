export interface MeaningAction {
  label: string;
  href?: string;
  action?: string;
}

export interface MeaningContext {
  what_happened: string;
  who: string;
  why_it_matters: string;
  what_next: string;
  actions?: MeaningAction[];
}

export interface ScreenContextResponse {
  screen: string;
  context: MeaningContext;
}
