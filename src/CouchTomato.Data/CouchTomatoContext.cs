using Microsoft.EntityFrameworkCore;

namespace CouchTomato.Data;

public class CouchTomatoContext : DbContext
{
    public CouchTomatoContext(DbContextOptions<CouchTomatoContext> options)
        : base(options) { }

    // public DbSet<Movie> Movies => Set<Movie>();  // add in later phases
}
