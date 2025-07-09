#![allow(unused_variables)]
use clap::Parser;
use tracing::{debug, error, info, trace, warn, Level};
use tracing_subscriber::{fmt, EnvFilter};
use crate::utils::{read_xml_file,_walk_tree};
use crate::cli::Args;
mod utils;
mod cli;
mod parser_manual;



fn main() {
    let filter = EnvFilter::from_default_env()
        .add_directive(Level::INFO.into());

    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .pretty()
        .init();


    let args = Args::parse();

    let content = read_xml_file(args.file).unwrap();
    let start_time = std::time::Instant::now();

    // _walk_tree(&content);

    let elapsed = start_time.elapsed();

    info!("Time to run walk of data: {:?}",elapsed.as_secs());
}






