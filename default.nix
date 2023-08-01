{ pkgs ? import <nixpkgs> {} }:

pkgs.poetry2nix.mkPoetryApplication {
  python = pkgs.python311;
  projectDir = ./.;
}