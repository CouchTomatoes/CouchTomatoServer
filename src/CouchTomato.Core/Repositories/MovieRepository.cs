using CouchTomato.Data;
using CouchTomato.Data.Entities;

namespace CouchTomato.Core.Repositories;

public class MovieRepository : EntityBaseRepository<Movie>
{
    public MovieRepository(CouchTomatoContext db) : base(db) { }
}
