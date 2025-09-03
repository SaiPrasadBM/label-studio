import * as React from "react";

export type ButtonSize = "small" | "compact" | string;
export type ButtonLook = string | string[];

export interface ButtonProps extends React.HTMLAttributes<HTMLElement> {
  children?: React.ReactNode;
  className?: string;
  rawClassName?: string;
  type?: string; // visual type used in BEM, not HTML button type
  size?: ButtonSize;
  waiting?: boolean;
  icon?: React.ReactElement<any> | null;
  tag?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  look?: ButtonLook;
  extra?: React.ReactNode;
  primary?: boolean;
  href?: string;
  disabled?: boolean;
}

export interface ButtonGroupProps {
  className?: string;
  children?: React.ReactNode;
  collapsed?: boolean;
}

export interface ButtonComponent
  extends React.ForwardRefExoticComponent<
    React.PropsWithoutRef<ButtonProps> & React.RefAttributes<any>
  > {
  Group: React.FC<ButtonGroupProps>;
}

export const Button: ButtonComponent;
