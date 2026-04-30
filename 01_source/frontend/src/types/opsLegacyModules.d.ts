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

/** JSX legado fora do strict-core (ex.: painéis de pickup). */
declare module "*.jsx" {
  import type { ComponentType } from "react";
  const component: ComponentType<Record<string, unknown>>;
  export default component;
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

