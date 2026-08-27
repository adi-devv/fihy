export const ESCALATION_STATES = ['drafted', 'sent', 'failed', 'bounced'] as const;
export type EscalationState = (typeof ESCALATION_STATES)[number];

/** The letter raised with the authority, as the people it was sent for may
 *  read it. The recipient address and reply token never leave the server. */
export type Escalation = {
  authority: string;
  state: EscalationState;
  subject: string;
  body: string;
  reference: string | null;
  detail: string | null;
  sent_at: string | null;
};

export const escalationLabel: Record<EscalationState, string> = {
  drafted: 'Drafted, not yet sent',
  sent: 'Sent',
  failed: 'Could not be sent',
  bounced: 'Bounced back',
};
