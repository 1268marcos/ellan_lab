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

