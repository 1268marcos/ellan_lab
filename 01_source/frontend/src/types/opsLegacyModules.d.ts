declare module "*services/authApi" {
  export function fetchPublicMe(token: string): Promise<unknown>;
  export function fetchPublicRoles(token: string): Promise<unknown>;
  export function loginPublicUser(payload: unknown): Promise<unknown>;
  export function registerPublicUser(payload: unknown): Promise<unknown>;
}

declare module "*OpsHelpTutorialModal" {
  interface TutorialSection {
    title: string;
    items: string[];
  }

  interface OpsHelpTutorialModalProps {
    title: string;
    subtitle?: string;
    sections: TutorialSection[];
    ctaLabel: string;
    ctaHref: string;
    storageKey: string;
    userKey: string;
  }

  const OpsHelpTutorialModal: (props: OpsHelpTutorialModalProps) => JSX.Element;
  export default OpsHelpTutorialModal;
}

declare module "*constants/opsTutorialContent" {
  interface TutorialSection {
    title: string;
    items: string[];
  }

  interface ResolvedTutorial {
    title: string;
    subtitle?: string;
    sections: TutorialSection[];
  }

  export function resolveOpsTutorial(currentOpsPath: string, currentOpsLink: unknown): ResolvedTutorial;
}

