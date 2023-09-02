{ pkgs ? import <nixpkgs> { } }:

let
  sqlite-zstd = pkgs.fetchzip {
    name = "sqlite-zstd";

    url = "https://github.com/phiresky/sqlite-zstd/releases/download/v0.3.2/sqlite_zstd-v0.3.2-x86_64-unknown-linux-gnu.tar.gz";
    sha256 = "sha256-WOdKxMEwLVw44mclic79qt8HoIKG6lXClg/AvXg3DiY=";
  };
in
pkgs.poetry2nix.mkPoetryApplication {
  python = pkgs.python311;
  projectDir = ./.;

  makeWrapperArgs = [
    "--set SQLITE_ZSTD_PATH $SQLITE_ZSTD_PATH"
  ];

  SQLITE_ZSTD_PATH = sqlite-zstd;
}
